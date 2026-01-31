from loguru import logger

from aitrados_api.common_lib.response_format import ErrorResponse
from aitrados_api.trade_middleware.request import FrontendRequest, AsyncFrontendRequest
from aitrados_api.trade_middleware_service.trade_middleware_rpc_service import AitradosApiBackendService


def rpc_request(backend_identity,fun_name,*args,**kwargs):
    try:
        result = FrontendRequest.call_sync(
            backend_identity,
            fun_name, *args, **kwargs,
        )
        return result
    except Exception as e:
        message = str(e)
        data = ErrorResponse(code=429, message=message, status="error").model_dump()
        return data

def rpc_request_and_forget(backend_identity,fun_name,*args,**kwargs):
    try:
        FrontendRequest.call_fire_and_forget(
            backend_identity,
            fun_name, *args, **kwargs,
        )
    except Exception as e:
        logger.warning(str(e))

        pass



async def a_rpc_request(backend_identity,fun_name,*args,**kwargs):
    try:
        result = await AsyncFrontendRequest.call_sync(
            backend_identity,
            fun_name, *args, **kwargs,
        )
        return result
    except Exception as e:
        message = str(e)
        data = ErrorResponse(code=429, message=message, status="error").model_dump()
        return data