from rest_framework.decorators import api_view, renderer_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from rest_framework.response import Response
from registro.models.models_global import Trazabilidad
from registro.serializer.serializer_get import TrazabilidadSerializer

from eco_back.utils import ServiceValidationError, handle_service_validation_error, _log_warn
 
 
 
@csrf_exempt
@api_view(['GET'])
@renderer_classes([JSONRenderer])
@handle_service_validation_error
def TrazabilidadRegistroPermiso(request, registro_id):
    try:
        trazabilidades = Trazabilidad.objects.filter(
            registro=int(registro_id)
        ).order_by('fecha_recibido')
 
        serializer = TrazabilidadSerializer(trazabilidades, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        _log_warn(f"Consulta trazabilidades - error consultando trazabilidades: {e}", level='error', exc_info=True)
        raise ServiceValidationError("Trazabilidades no encontradas", code=400, context={"exception": str(e)})