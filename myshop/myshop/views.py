from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


def page_not_found(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "404.html", status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    return render(request, "500.html", status=500)


def permission_denied(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "403.html", status=403)


def bad_request(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "400.html", status=400)


@require_GET
def bad_gateway(request: HttpRequest) -> HttpResponse:
    """
    Explicit 502 error page, reachable via /502/ or /en/502/.

    Use this for maintenance mode, health-check redirects, or when the
    reverse proxy detects upstream failure and rewrites the request to
    this URL so Django can render the branded 502 page.

    NOTE: A true 502 Bad Gateway (proxy cannot reach Django at all)
    CANNOT be served by Django. Configure your reverse proxy (Caddy,
    nginx) to serve a static 502.html when the upstream is down.
    """
    return render(request, "502.html", status=502)


@csrf_exempt
@require_GET
def maintenance(request: HttpRequest) -> HttpResponse:
    """
    Maintenance-mode endpoint. Returns the branded 502 template.

    Wire your reverse proxy to serve this page during deployments via
    rewriting /any-path to this endpoint, or by enabling maintenance
    mode through a load-balancer health check.
    """
    return render(request, "502.html", status=503)


@require_GET
def healthz(request: HttpRequest) -> HttpResponse:
    """Liveness/readiness probe for Coolify. 200 if the DB is reachable.

    Doesn't check Redis: sessions use cached_db (SESSION_ENGINE), so a Redis
    outage degrades gracefully rather than being a hard failure — treating
    it as one here would make routine Redis blips look like a full outage.
    """
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return HttpResponse(status=503)
    return HttpResponse("ok")
