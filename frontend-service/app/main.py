import os

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import httpx

# Базовые URL микросервисов
AUTH_BASE = os.getenv("AUTH_BASE", "http://auth_service:8001")
PROPERTY_BASE = os.getenv("PROPERTY_BASE", "http://property_service:8002")
LEASING_BASE = os.getenv("LEASING_BASE", "http://leasing_service:8003")

app = FastAPI(title="Rental Frontend")

templates = Jinja2Templates(directory="app/templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="supersecret_frontend_key")


def get_token_from_cookies(request: Request) -> str | None:
    return request.cookies.get("access_token")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # если есть токен — сразу в список объектов
    token = get_token_from_cookies(request)
    if token:
        return RedirectResponse(url="/properties")
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{AUTH_BASE}/api/v1/auth/login",
                json={"email": email, "password": password},
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Сервис авторизации недоступен",
                },
                status_code=503,
            )

    if resp.status_code not in (200, 201):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Неверный логин или пароль",
            },
            status_code=400,
        )

    data = resp.json()
    token = data.get("access_token")
    if not token:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Не удалось получить токен",
            },
            status_code=500,
        )

    response = RedirectResponse(url="/properties", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60,
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@app.get("/properties", response_class=HTMLResponse)
async def properties_list(request: Request):
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login")

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{PROPERTY_BASE}/api/v1/properties/",
                headers=headers,
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "properties.html",
                {
                    "request": request,
                    "properties": [],
                    "error": "Сервис объектов недоступен",
                },
                status_code=503,
            )

    if resp.status_code == 401:
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie("access_token")
        return response

    if resp.status_code not in (200, 201):
        return templates.TemplateResponse(
            "properties.html",
            {
                "request": request,
                "properties": [],
                "error": f"Ошибка сервиса объектов: {resp.status_code}",
            },
            status_code=resp.status_code,
        )

    properties = resp.json()
    return templates.TemplateResponse(
        "properties.html",
        {
            "request": request,
            "properties": properties,
            "error": None,
        },
    )
