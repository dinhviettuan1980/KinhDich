import logging
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from . import db as dbmod
from . import devices
from .device_bus import get_bus
from .scheduler import Scheduler
from .config import BASE_DIR, get_settings
from .routers import admin, auth, booking, device_api, orders, public
from .web import LoginRequired, render, u

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    if dbmod.engine is None:
        dbmod.init_engine()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        bus = get_bus()
        bus.start(devices.handle_message)
        sched = None
        if settings.scheduler_enabled:
            sched = Scheduler(settings.scheduler_interval_seconds)
            sched.start()
        yield
        if sched:
            sched.stop()
        bus.stop()

    app = FastAPI(title="Linh Địa Việt", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(
        SessionMiddleware, secret_key=settings.secret_key, session_cookie="ld_session",
        path=settings.prefix or "/", same_site="lax", https_only=settings.session_https_only,
        max_age=14 * 24 * 3600,
    )
    p = settings.prefix
    app.mount(f"{p}/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    for r in (public.router, auth.router, booking.router, orders.router, admin.router, device_api.router):
        app.include_router(r, prefix=p)

    @app.get(f"{p}/manifest.webmanifest", include_in_schema=False)
    def manifest():
        """PWA: cài lên màn hình chính điện thoại (Safari → Chia sẻ → Thêm vào MH chính), mở toàn màn hình như app."""
        icon = lambda name, size, purpose="any": {"src": u(f"/static/icons/{name}"), "sizes": f"{size}x{size}",  # noqa: E731
                                                   "type": "image/png", "purpose": purpose}
        return JSONResponse({
            "name": "Linh Địa Việt – Lễ chùa từ xa", "short_name": "Lễ chùa", "lang": "vi",
            "description": "Đặt lễ, dâng sớ và xem lại video lễ tại đền chùa từ xa.",
            "id": u("/"), "start_url": u("/"), "scope": u("/"), "display": "standalone",
            "background_color": "#faf6ee", "theme_color": "#7a1f1f",
            "icons": [icon("icon-192.png", 192), icon("icon-512.png", 512),
                      icon("icon-maskable-512.png", 512, "maskable")],
        }, media_type="application/manifest+json")

    if p:
        @app.get("/", include_in_schema=False)
        def root():
            return RedirectResponse(u("/"))

    @app.exception_handler(LoginRequired)
    async def _login_required(request: Request, exc: LoginRequired):
        nxt = request.url.path + (f"?{request.url.query}" if request.url.query else "")
        return RedirectResponse(u("/dang-nhap") + "?next=" + quote(nxt), 303)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        wants_html = "text/html" in request.headers.get("accept", "") and not request.headers.get("hx-request")
        if wants_html and exc.status_code in (400, 403, 404, 409, 429):
            return render(request, "error.html", {"code": exc.status_code, "detail": exc.detail},
                          status_code=exc.status_code)
        return await http_exception_handler(request, exc)

    return app


app = create_app()
