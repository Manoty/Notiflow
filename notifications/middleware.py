import time
import uuid
import logging

logger = logging.getLogger('notifications.requests')


class RequestLoggingMiddleware:
    """
    Logs every inbound request and outbound response as structured JSON.

    Adds X-Request-ID header to every response — lets you correlate
    a client-side error with the exact server log line that caused it.

    Logs at INFO for 2xx/3xx, WARNING for 4xx, ERROR for 5xx.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id

        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = round((time.monotonic() - start) * 1000, 1)
        status      = response.status_code

        log_data = {
            'request_id': request_id,
            'method':     request.method,
            'path':       request.path,
            'status':     status,
            'duration_ms': duration_ms,
            'app_id':     getattr(request, 'app_id', None),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:120],
            'ip':         self._get_ip(request),
        }

        if status >= 500:
            logger.error('request completed', extra=log_data)
        elif status >= 400:
            logger.warning('request completed', extra=log_data)
        else:
            logger.info('request completed', extra=log_data)

        response['X-Request-ID'] = request_id
        return response

    def _get_ip(self, request) -> str:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')