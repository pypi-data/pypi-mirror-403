"""
Tests para el módulo de anexos y documentos
"""
import pytest
import tempfile
import os
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock

from eco_back.documento import AnexoManager, AnexoConfig, DocumentoResult


@pytest.fixture
def config_basica():
    """Configuración básica para tests"""
    return AnexoConfig(
        url_base="https://api.test.com",
        max_size=1024 * 1024,  # 1MB para tests
        max_retries=2,
        timeout=10
    )


@pytest.fixture
def manager(config_basica):
    """Fixture del manager"""
    return AnexoManager(config_basica)


def test_obtener_extension(manager):
    """Test de obtención de extensión"""
    assert manager.obtener_extension("archivo.pdf") == ".pdf"
    assert manager.obtener_extension("documento.PDF") == ".pdf"
    assert manager.obtener_extension("imagen.JPG") == ".jpg"
    assert manager.obtener_extension("sin_extension") == ""


def test_validar_extension(manager):
    """Test de validación de extensiones"""
    assert manager.validar_extension(".pdf") is True
    assert manager.validar_extension("pdf") is True
    assert manager.validar_extension(".jpg") is True
    assert manager.validar_extension(".exe") is False
    assert manager.validar_extension(".bat") is False


def test_obtener_mime_type(manager):
    """Test de obtención de tipo MIME"""
    assert manager.obtener_mime_type("doc.pdf") == "application/pdf"
    assert manager.obtener_mime_type("foto.jpg") == "image/jpeg"
    assert manager.obtener_mime_type("foto.jpeg") == "image/jpeg"
    assert manager.obtener_mime_type("imagen.png") == "image/png"
    assert manager.obtener_mime_type("archivo.xyz") == "application/octet-stream"


def test_documento_result():
    """Test de DocumentoResult"""
    resultado = DocumentoResult(
        status="success",
        mensaje="Todo bien",
        detalles={"key": "value"}
    )
    
    assert resultado.status == "success"
    assert resultado.exitoso is True
    assert resultado.detalles["key"] == "value"
    
    dict_result = resultado.to_dict()
    assert dict_result["status"] == "success"
    assert dict_result["exitoso"] is True


def test_documento_result_error():
    """Test de DocumentoResult con error"""
    resultado = DocumentoResult(
        status="error",
        mensaje="Falló",
    )
    
    assert resultado.exitoso is False


def test_guardar_anexo_extension_invalida(manager):
    """Test de rechazo por extensión inválida"""
    archivo = BytesIO(b"contenido")
    
    resultado = manager.guardar_anexo(
        archivo=archivo,
        nombre_archivo="malware.exe",
        llave="123",
        grupo="test",
        tipo_documento="doc",
        diccionario=1,
        asincrono=False
    )
    
    assert resultado.exitoso is False
    assert "no permitida" in resultado.mensaje


def test_guardar_anexo_tamano_excedido(manager):
    """Test de rechazo por tamaño excedido"""
    # Crear contenido que excede el límite
    contenido = b"X" * (2 * 1024 * 1024)  # 2MB (límite es 1MB)
    
    resultado = manager.guardar_anexo(
        archivo=contenido,
        nombre_archivo="grande.pdf",
        llave="123",
        grupo="test",
        tipo_documento="doc",
        diccionario=1,
        asincrono=False
    )
    
    assert resultado.exitoso is False
    assert "excede tamaño" in resultado.mensaje


def test_escanear_archivo_sin_funcion(manager):
    """Test de escaneo cuando no hay función configurada"""
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(b"PDF content")
        tmp.flush()
        
        scan_result = manager._escanear_archivo(tmp.name, ".pdf")
        assert scan_result['status'] == 'CLEAN'


def test_escanear_archivo_con_funcion():
    """Test de escaneo con función personalizada"""
    def scan_mock(path, ext):
        return {'status': 'CLEAN', 'details': 'OK'}
    
    config = AnexoConfig(
        url_base="https://test.com",
        scan_function=scan_mock
    )
    manager = AnexoManager(config)
    
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(b"PDF content")
        tmp.flush()
        
        scan_result = manager._escanear_archivo(tmp.name, ".pdf")
        assert scan_result['status'] == 'CLEAN'


def test_obtener_endpoint(manager):
    """Test de obtención de endpoint según diccionario"""
    assert manager._obtener_endpoint(1) == "usuario"
    assert manager._obtener_endpoint(2) == "persona"
    assert manager._obtener_endpoint(3) == "colectivo"
    assert manager._obtener_endpoint(99) == "usuario"  # Default


def test_obtener_tipo_documento_sin_diccionario(manager):
    """Test de tipo de documento sin función de diccionario"""
    tipo = manager._obtener_tipo_documento("cedula", 1)
    assert tipo == "cedula"  # Sin mapeo, devuelve original


def test_obtener_tipo_documento_con_diccionario():
    """Test de tipo de documento con función de diccionario"""
    def dict_func(tipo):
        return {"cedula": "CC"}.get(tipo, tipo)
    
    config = AnexoConfig(
        url_base="https://test.com",
        diccionario_registro=dict_func
    )
    manager = AnexoManager(config)
    
    tipo = manager._obtener_tipo_documento("cedula", 1)
    assert tipo == "CC"


@patch('eco_back.documento.anexos.requests.post')
def test_enviar_documento_sincrono_exitoso(mock_post, manager):
    """Test de envío síncrono exitoso"""
    # Mock de respuesta exitosa
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_response.content = b'{"success": true}'
    mock_post.return_value = mock_response
    
    # Crear archivo temporal
    with tempfile.TemporaryDirectory() as temp_dir:
        archivo_path = os.path.join(temp_dir, "test.pdf")
        with open(archivo_path, 'wb') as f:
            f.write(b"PDF content")
        
        file_meta = {
            'field': 'anexo',
            'path': archivo_path,
            'original_name': 'test.pdf',
            'tipo_documento': 'cedula'
        }
        
        resultado = manager._enviar_documento_sincrono(
            file_meta=file_meta,
            llave="123",
            grupo="test",
            tipo="cedula",
            temp_dir=temp_dir,
            diccionario=1
        )
        
        assert resultado.exitoso is True
        assert resultado.status == "success"
        assert mock_post.called


@patch('eco_back.documento.anexos.requests.post')
def test_enviar_documento_con_reintentos(mock_post, manager):
    """Test de reintentos en caso de error del servidor"""
    # Primera llamada falla con 500, segunda con 200
    mock_response_error = Mock()
    mock_response_error.status_code = 500
    
    mock_response_ok = Mock()
    mock_response_ok.status_code = 200
    mock_response_ok.json.return_value = {"success": True}
    mock_response_ok.content = b'{"success": true}'
    
    mock_post.side_effect = [mock_response_error, mock_response_ok]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        archivo_path = os.path.join(temp_dir, "test.pdf")
        with open(archivo_path, 'wb') as f:
            f.write(b"PDF content")
        
        file_meta = {
            'field': 'anexo',
            'path': archivo_path,
            'original_name': 'test.pdf',
            'tipo_documento': 'cedula'
        }
        
        resultado = manager._enviar_documento_sincrono(
            file_meta=file_meta,
            llave="123",
            grupo="test",
            tipo="cedula",
            temp_dir=temp_dir,
            diccionario=1
        )
        
        assert resultado.exitoso is True
        assert mock_post.call_count == 2


@patch('eco_back.documento.anexos.requests.post')
def test_guardar_anexo_asincrono(mock_post, manager):
    """Test de guardado asíncrono"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_response.content = b'{"success": true}'
    mock_post.return_value = mock_response
    
    contenido = b"PDF content"
    
    resultado = manager.guardar_anexo(
        archivo=contenido,
        nombre_archivo="test.pdf",
        llave="123",
        grupo="test",
        tipo_documento="cedula",
        diccionario=1,
        asincrono=True
    )
    
    assert resultado.exitoso is True
    assert resultado.status == "processing"
    assert "proceso" in resultado.mensaje
