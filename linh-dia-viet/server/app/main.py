import logging
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from . import db as dbmod
from .config import BASE_DIR, get_settings
from .routers import admin, auth, public
from .web import LoginRequired, render, u

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    if dbmod.engine is None:
        dbmod.init_engine()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    app = FastAPI(title="Linh Địa Việt", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(
        SessionMiddleware, secret_key=settings.secret_key, session_cookie="ld_session",
        path=settings.prefix or "/", same_site="lax", https_only=settings.session_https_only,
        max_age=14 * 24 * 3600,
    )
    p = settings.prefix
    app.mount(f"{p}/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    for r in (public.router, auth.router, admin.router):
        app.include_router(r, prefix=p)

    if p:
        @app.get("/", include_in_schema=False)
        def root():
            return RedirectResponse(u("/"))

    @app.exception_handler(LoginRequired)
    async def _login_required(request: Request, exc: LoginRequired):
        return RedirectResponse(u("/dang-nhap") + "?next=" + quote(str(request.url.path)), 303)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        wants_html = "text/html" in request.headers.get("accept", "") and not request.headers.get("hx-request")
        if wants_html and exc.status_code in (400, 403, 404, 409, 429):
            return render(request, "error.html", {"code": exc.status_code, "detail": exc.detail},
                          status_code=exc.status_code)
        return await http_exception_handler(request, exc)

    return app


app = create_app()
