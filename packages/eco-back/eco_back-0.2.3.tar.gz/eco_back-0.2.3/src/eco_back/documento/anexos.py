"""
Cliente para gestión de anexos y documentos UNP

Maneja el proceso de validación, escaneo y envío de documentos
a los servicios de la API UNP.
"""
import logging
import os
import shutil
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable, BinaryIO, Union
from io import BytesIO

import requests

logger = logging.getLogger(__name__)


# Constantes
MAX_SIZE = 10 * 1024 * 1024  # 10MB
MAX_RETRIES = 3
TIMEOUT = 30

# Extensiones MIME permitidas
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}


@dataclass
class AnexoConfig:
    """
    Configuración para el gestor de anexos
    
    Attributes:
        url_base: URL base del API UNP
        max_size: Tamaño máximo de archivo en bytes (default: 10MB)
        max_retries: Número máximo de reintentos (default: 3)
        timeout: Timeout para las peticiones en segundos (default: 30)
        scan_function: Función opcional para escaneo de archivos
        diccionario_registro: Función para mapear tipos de documento de registro
        diccionario_persona: Función para mapear tipos de documento de persona
        diccionario_colectivo: Función para mapear tipos de documento de colectivo
    """
    url_base: str
    max_size: int = MAX_SIZE
    max_retries: int = MAX_RETRIES
    timeout: int = TIMEOUT
    scan_function: Optional[Callable] = None
    diccionario_registro: Optional[Callable] = None
    diccionario_persona: Optional[Callable] = None
    diccionario_colectivo: Optional[Callable] = None


class DocumentoResult:
    """Resultado del procesamiento de un documento"""
    
    def __init__(self, status: str, mensaje: str, detalles: Optional[Dict] = None):
        self.status = status
        self.mensaje = mensaje
        self.detalles = detalles or {}
        self.exitoso = status in ['success', 'processing']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        return {
            'status': self.status,
            'mensaje': self.mensaje,
            'detalles': self.detalles,
            'exitoso': self.exitoso
        }


class AnexoManager:
    """
    Gestor de anexos y documentos para la API UNP
    
    Maneja el proceso completo de:
    - Validación de archivos
    - Escaneo antivirus (opcional)
    - Envío asíncrono a la API UNP
    
    Ejemplo:
        >>> from eco_back.documento import AnexoManager, AnexoConfig
        >>> 
        >>> config = AnexoConfig(url_base="https://api.unp.gov.co")
        >>> manager = AnexoManager(config)
        >>> 
        >>> # Subir archivo desde ruta
        >>> with open("documento.pdf", "rb") as f:
        ...     resultado = manager.guardar_anexo(
        ...         archivo=f,
        ...         nombre_archivo="documento.pdf",
        ...         llave="12345",
        ...         grupo="grupo1",
        ...         tipo_documento="cedula",
        ...         diccionario=1
        ...     )
        >>> print(resultado.mensaje)
    """
    
    def __init__(self, config: AnexoConfig):
        """
        Inicializa el gestor de anexos
        
        Args:
            config: Configuración del gestor
        """
        self.config = config
    
    def obtener_extension(self, nombre_archivo: str) -> str:
        """
        Obtiene la extensión del archivo (incluye el punto, ej: '.pdf')
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Extensión del archivo en minúsculas (con punto)
        """
        return os.path.splitext(nombre_archivo)[1].lower()
    
    def validar_extension(self, extension: str) -> bool:
        """
        Valida si la extensión es permitida
        
        Args:
            extension: Extensión a validar (con o sin punto)
            
        Returns:
            True si es válida, False en caso contrario
        """
        ext = extension.lstrip('.')
        return ext in ALLOWED_EXTENSIONS
    
    def obtener_mime_type(self, nombre_archivo: str) -> str:
        """
        Obtiene el tipo MIME basado en la extensión del archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Tipo MIME correspondiente
        """
        ext = nombre_archivo.split('.')[-1].lower()
        return ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')
    
    def _escanear_archivo(self, ruta_archivo: str, extension: str) -> Dict[str, Any]:
        """
        Escanea el archivo en busca de amenazas
        
        Args:
            ruta_archivo: Ruta del archivo a escanear
            extension: Extensión del archivo
            
        Returns:
            Diccionario con status y detalles del escaneo
        """
        if self.config.scan_function:
            try:
                return self.config.scan_function(ruta_archivo, extension)
            except Exception as e:
                logger.error(f"Error en escaneo: {e}")
                return {'status': 'ERROR', 'details': str(e)}
        
        # Sin función de escaneo, asumir limpio
        return {'status': 'CLEAN', 'details': 'No scan configured'}
    
    def guardar_anexo(
        self,
        archivo: Union[BinaryIO, BytesIO, bytes],
        nombre_archivo: str,
        llave: str,
        grupo: str,
        tipo_documento: str,
        diccionario: int,
        asincrono: bool = True
    ) -> DocumentoResult:
        """
        Guarda y envía un anexo a la API UNP
        
        Args:
            archivo: Archivo a subir (file-like object o bytes)
            nombre_archivo: Nombre original del archivo
            llave: Identificador único del registro
            grupo: Grupo del documento
            tipo_documento: Tipo de documento a enviar
            diccionario: Tipo de diccionario (1=registro, 2=persona, 3=colectivo)
            asincrono: Si True, envía en hilo separado (default: True)
            
        Returns:
            DocumentoResult con el resultado del procesamiento
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Validar extensión
            extension = self.obtener_extension(nombre_archivo)
            if not self.validar_extension(extension):
                return DocumentoResult(
                    status='error',
                    mensaje=f"Extensión {extension} no permitida",
                    detalles={'extensiones_permitidas': list(ALLOWED_EXTENSIONS.keys())}
                )
            
            # Leer contenido del archivo
            if isinstance(archivo, bytes):
                contenido = archivo
            else:
                contenido = archivo.read()
            
            # Validar tamaño
            if len(contenido) > self.config.max_size:
                return DocumentoResult(
                    status='error',
                    mensaje=f"Archivo excede tamaño máximo de {self.config.max_size / 1024 / 1024}MB",
                    detalles={'tamaño': len(contenido), 'max_size': self.config.max_size}
                )
            
            # Guardar temporalmente
            with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=extension) as tmp:
                tmp.write(contenido)
                temp_path = tmp.name
            
            # Escaneo antivirus
            scan_result = self._escanear_archivo(temp_path, extension)
            if scan_result['status'] != "CLEAN":
                os.remove(temp_path)
                shutil.rmtree(temp_dir, ignore_errors=True)
                return DocumentoResult(
                    status='blocked',
                    mensaje=f"Archivo {nombre_archivo} bloqueado por escaneo",
                    detalles=scan_result
                )
            
            # Renombrar archivo con timestamp
            ext = extension.lstrip('.') or 'bin'
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            nuevo_nombre = f"{llave}_anexo_{timestamp}.{ext}"
            destino = os.path.join(temp_dir, nuevo_nombre)
            os.replace(temp_path, destino)
            
            file_meta = {
                'field': 'anexo',
                'path': destino,
                'original_name': nombre_archivo,
                'tipo_documento': tipo_documento,
            }
            
            # Enviar archivo
            if asincrono:
                threading.Thread(
                    target=self._enviar_documento,
                    args=(file_meta, llave, grupo, tipo_documento, temp_dir, diccionario)
                ).start()
                
                return DocumentoResult(
                    status='processing',
                    mensaje='Documento en proceso de envío',
                    detalles={'archivo': nuevo_nombre}
                )
            else:
                # Envío síncrono
                resultado = self._enviar_documento_sincrono(
                    file_meta, llave, grupo, tipo_documento, temp_dir, diccionario
                )
                return resultado
        
        except Exception as e:
            logger.error(f"Error en guardar_anexo: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return DocumentoResult(
                status='error',
                mensaje=str(e),
                detalles={'error_type': type(e).__name__}
            )
    
    def _obtener_tipo_documento(self, tipo: str, diccionario: int) -> Optional[str]:
        """
        Obtiene el tipo de documento usando el diccionario correspondiente
        
        Args:
            tipo: Tipo de documento original
            diccionario: Tipo de diccionario (1=registro, 2=persona, 3=colectivo)
            
        Returns:
            Tipo de documento mapeado o None
        """
        if diccionario == 1 and self.config.diccionario_registro:
            return self.config.diccionario_registro(tipo)
        elif diccionario == 2 and self.config.diccionario_persona:
            return self.config.diccionario_persona(tipo)
        elif diccionario == 3 and self.config.diccionario_colectivo:
            return self.config.diccionario_colectivo(tipo)
        
        # Si no hay diccionario, devolver el tipo original
        return tipo
    
    def _obtener_endpoint(self, diccionario: int) -> str:
        """
        Obtiene el endpoint según el tipo de diccionario
        
        Args:
            diccionario: Tipo de diccionario (1=registro, 2=persona, 3=colectivo)
            
        Returns:
            Endpoint correspondiente
        """
        endpoints = {
            1: 'usuario',
            2: 'persona',
            3: 'colectivo'
        }
        return endpoints.get(diccionario, 'usuario')
    
    def _enviar_documento(
        self,
        file_meta: Dict[str, str],
        llave: str,
        grupo: str,
        tipo: str,
        temp_dir: str,
        diccionario: int
    ) -> None:
        """
        Envía el documento a la API UNP (versión asíncrona)
        
        Args:
            file_meta: Metadatos del archivo
            llave: Identificador del registro
            grupo: Grupo del documento
            tipo: Tipo de documento
            temp_dir: Directorio temporal
            diccionario: Tipo de diccionario
        """
        try:
            resultado = self._enviar_documento_sincrono(
                file_meta, llave, grupo, tipo, temp_dir, diccionario
            )
            if resultado.exitoso:
                logger.info(f"Documento enviado exitosamente: {file_meta['original_name']}")
            else:
                logger.error(f"Error enviando documento: {resultado.mensaje}")
        except Exception as e:
            logger.error(f"Error en envío asíncrono: {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _enviar_documento_sincrono(
        self,
        file_meta: Dict[str, str],
        llave: str,
        grupo: str,
        tipo: str,
        temp_dir: str,
        diccionario: int
    ) -> DocumentoResult:
        """
        Envía el documento a la API UNP de forma síncrona
        
        Args:
            file_meta: Metadatos del archivo
            llave: Identificador del registro
            grupo: Grupo del documento
            tipo: Tipo de documento
            temp_dir: Directorio temporal
            diccionario: Tipo de diccionario
            
        Returns:
            DocumentoResult con el resultado del envío
        """
        try:
            if not os.path.exists(file_meta['path']):
                return DocumentoResult(
                    status='error',
                    mensaje=f"Archivo no encontrado: {file_meta['path']}"
                )
            
            # Leer contenido
            with open(file_meta['path'], 'rb') as f:
                content = f.read()
                if len(content) > self.config.max_size:
                    return DocumentoResult(
                        status='error',
                        mensaje=f"Archivo {file_meta['original_name']} excede tamaño permitido"
                    )
            
            # Determinar MIME
            mime_type = self.obtener_mime_type(file_meta['original_name'])
            
            # Preparar archivos para envío
            files = [
                (file_meta['field'], (file_meta['original_name'], content, mime_type))
            ]
            
            # Headers
            headers = {
                'User-Agent': 'EcoBack-DocumentSender/1.0',
                'X-Request-ID': str(uuid.uuid4())
            }
            
            # Obtener endpoint y tipo de documento
            endpoint = self._obtener_endpoint(diccionario)
            tipo_docu = self._obtener_tipo_documento(tipo, diccionario)
            
            # URL completa
            url = f"{self.config.url_base}/api-doc/{endpoint}/guardaranexo"
            
            # Datos del formulario
            data = {
                'llave': llave,
                'grupo': grupo,
                'tipo_documento': tipo_docu
            }
            
            # Envío con reintentos
            for intento in range(self.config.max_retries):
                try:
                    response = requests.post(
                        url,
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=self.config.timeout
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Envío exitoso en intento {intento + 1}")
                        return DocumentoResult(
                            status='success',
                            mensaje='Documento enviado exitosamente',
                            detalles={
                                'intentos': intento + 1,
                                'response': response.json() if response.content else {}
                            }
                        )
                    elif 500 <= response.status_code < 600:
                        # Error del servidor, reintentar
                        logger.warning(f"Error del servidor ({response.status_code}), reintentando...")
                        time.sleep(2 ** intento)
                        continue
                    else:
                        # Error del cliente, no reintentar
                        return DocumentoResult(
                            status='error',
                            mensaje=f"Error en envío: {response.status_code}",
                            detalles={'response_text': response.text}
                        )
                
                except requests.RequestException as e:
                    logger.error(f"Error de conexión en intento {intento + 1}: {e}")
                    if intento == self.config.max_retries - 1:
                        return DocumentoResult(
                            status='error',
                            mensaje='Máximo número de reintentos alcanzado',
                            detalles={'error': str(e)}
                        )
                    time.sleep(2 ** intento)
            
            return DocumentoResult(
                status='error',
                mensaje='No se pudo enviar el documento después de todos los reintentos'
            )
        
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
