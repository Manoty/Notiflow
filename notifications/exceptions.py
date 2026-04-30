import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('notifications.exceptions')


def notiflow_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler to ensure every error
    response uses our consistent shape:
        { success: false, error: "...", code: "..." }

    Also logs server errors (5xx) with full context so they appear
    in the structured log file alongside request metadata.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_msg = _extract_message(response.data)
        response.data = {
            'success': False,
            'error':   error_msg,
            'code':    _status_to_code(response.status_code),
        }
        return response

    # Unhandled exception → 500
    request = context.get('request')
    logger.exception(
        'Unhandled exception in view',
        extra={
            'view':   context.get('view', '').__class__.__name__,
            'method': getattr(request, 'method', ''),
            'path':   getattr(request, 'path', ''),
        },
        exc_info=exc,
    )
    return Response(
        {
            'success': False,
            'error':   'An unexpected error occurred. It has been logged.',
            'code':    'internal_server_error',
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_message(data) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ('detail', 'error', 'message', 'non_field_errors'):
            if key in data:
                val = data[key]
                if isinstance(val, list):
                    return str(val[0])
                return str(val)
        first_val = next(iter(data.values()), '')
        if isinstance(first_val, list):
            return str(first_val[0])
        return str(first_val)
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)


def _status_to_code(status_code: int) -> str:
    return {
        400: 'bad_request',
        401: 'unauthorized',
        403: 'forbidden',
        404: 'not_found',
        405: 'method_not_allowed',
        429: 'rate_limit_exceeded',
        500: 'internal_server_error',
    }.get(status_code, f'http_{status_code}')