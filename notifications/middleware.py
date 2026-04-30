import time
import uuid
import logging
from django.http import JsonResponse
from django.conf import settings
from collections import defaultdict
from threading import Lock


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
    
    
class APIKeyMiddleware:
    """
    Validates X-API-Key header on all /notifications/ endpoints.
    Resolves the key to an app_id and attaches it to request.app_id.

    Exemptions:
        /health/        — monitoring tools don't carry API keys
        /admin/         — uses Django's own session auth
        GET /notifications/  — read-only listing, relaxed for dashboard

    On success:  request.app_id is set, request proceeds
    On missing:  401 Unauthorized
    On invalid:  403 Forbidden
    """

    EXEMPT_PATHS = ('/health/', '/admin/')
    EXEMPT_METHODS_PATHS = (
        ('GET', '/notifications/'),
        ('GET', '/notifications/inbox/'),
        ('GET', '/notifications/unread-count/'),
        ('GET', '/notifications/queue-stats/'),
        ('GET', '/notifications/failed/'),
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self._keys: dict = {}

    def __call__(self, request):
        # Reload keys each request so .env changes don't need a restart
        self._keys = getattr(settings, 'NOTIFLOW_API_KEYS', {})

        if self._is_exempt(request):
            request.app_id = None
            return self.get_response(request)

        api_key = (
            request.META.get('HTTP_X_API_KEY')
            or request.GET.get('api_key')    # fallback for curl convenience
        )

        if not api_key:
            return JsonResponse(
                {
                    'success': False,
                    'error':   'Missing API key. Provide X-API-Key header.',
                    'code':    'missing_api_key',
                },
                status=401,
            )

        app_id = self._keys.get(api_key)
        if not app_id:
            logger.warning(
                'Invalid API key attempt',
                extra={'path': request.path, 'key_prefix': api_key[:8] + '…'},
            )
            return JsonResponse(
                {
                    'success': False,
                    'error':   'Invalid API key.',
                    'code':    'invalid_api_key',
                },
                status=403,
            )

        request.app_id = app_id
        return self.get_response(request)

    def _is_exempt(self, request) -> bool:
        if any(request.path.startswith(p) for p in self.EXEMPT_PATHS):
            return True
        for method, path in self.EXEMPT_METHODS_PATHS:
            if request.method == method and request.path.startswith(path):
                return True
        return False    
    
    
class RateLimitMiddleware:
    """
    Simple in-process sliding window rate limiter.
    Keyed by API key (or IP for unauthenticated requests).
    Default: 60 requests per 60-second window.

    Production note: this uses in-process memory, so it resets
    on restart and doesn't share state across multiple workers.
    For multi-process deployments, replace the store with Redis:
        redis_client.incr(key); redis_client.expire(key, 60)
    The interface here is designed so that swap is straightforward.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._store: dict[str, list[float]] = defaultdict(list)
        self._lock  = Lock()

    def __call__(self, request):
        from django.conf import settings
        limit  = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60)
        window = 60.0

        key = self._get_key(request)
        now = time.monotonic()

        with self._lock:
            hits = self._store[key]

            # Evict timestamps outside the window
            self._store[key] = [t for t in hits if now - t < window]

            if len(self._store[key]) >= limit:
                retry_after = int(window - (now - self._store[key][0])) + 1
                logger.warning(
                    'Rate limit exceeded',
                    extra={
                        'key':         key[:16],
                        'limit':       limit,
                        'retry_after': retry_after,
                        'path':        request.path,
                    }
                )
                response = JsonResponse(
                    {
                        'success': False,
                        'error':   f'Rate limit exceeded. Try again in {retry_after}s.',
                        'code':    'rate_limit_exceeded',
                        'retry_after_seconds': retry_after,
                    },
                    status=429,
                )
                response['Retry-After'] = str(retry_after)
                return response

            self._store[key].append(now)

        return self.get_response(request)

    def _get_key(self, request) -> str:
        api_key = request.META.get('HTTP_X_API_KEY', '')
        if api_key:
            return f'key:{api_key[:16]}'
        return f'ip:{request.META.get("REMOTE_ADDR", "unknown")}'    