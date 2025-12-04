import os

from fastapi import FastAPI, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import httpx
import jwt

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


def get_user_id_from_token(token: str) -> int | None:
    """
    Достаём user_id из payload токена.
    Предполагаем, что в claim 'sub' лежит id пользователя (как обычно в FastAPI-примерах).
    Верификацию подписи не делаем, так как токен уже выдан нашим auth-service.
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
        )
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except Exception:
        return None



@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
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


@app.get("/properties/new", response_class=HTMLResponse)
async def property_new_form(request: Request):
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "property_form.html",
        {"request": request, "error": None},
    )


@app.post("/properties/new", response_class=HTMLResponse)
async def property_create(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    description: str = Form(""),
    property_type: str = Form("OFFICE"),
):
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login")

    owner_id = get_user_id_from_token(token)
    if owner_id is None:
        # что-то не так с токеном — отправим на логин
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie("access_token")
        return response

    headers = {"Authorization": f"Bearer {token}"}
    json_data = {
        "owner_id": owner_id,  # <-- автоматически из токена
        "name": name,
        "address": address,
        "description": description,
        "property_type": property_type,
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{PROPERTY_BASE}/api/v1/properties/",
                headers=headers,
                json=json_data,
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "property_form.html",
                {
                    "request": request,
                    "error": "Сервис объектов недоступен",
                },
                status_code=503,
            )

    if resp.status_code not in (200, 201):
        return templates.TemplateResponse(
            "property_form.html",
            {
                "request": request,
                "error": f"Ошибка создания объекта: {resp.status_code} {resp.text}",
            },
            status_code=resp.status_code,
        )

    return RedirectResponse(url="/properties", status_code=303)


@app.get("/properties/{property_id}/units", response_class=HTMLResponse)
async def units_list(
    request: Request,
    property_id: int,
    property_name: str | None = Query(default=None),
):
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login")

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            resp_units = await client.get(
                f"{PROPERTY_BASE}/api/v1/units/",
                headers=headers,
                params={"property_id": property_id},
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "units.html",
                {
                    "request": request,
                    "property_id": property_id,
                    "property_name": property_name,
                    "units": [],
                    "error": "Сервис помещений недоступен",
                },
                status_code=503,
            )

    if resp_units.status_code == 401:
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie("access_token")
        return response

    if resp_units.status_code not in (200, 201):
        return templates.TemplateResponse(
            "units.html",
            {
                "request": request,
                "property_id": property_id,
                "property_name": property_name,
                "units": [],
                "error": f"Ошибка сервиса помещений: {resp_units.status_code}",
            },
            status_code=resp_units.status_code,
        )

    units = resp_units.json()
    return templates.TemplateResponse(
        "units.html",
        {
            "request": request,
            "property_id": property_id,
            "property_name": property_name,
            "units": units,
            "error": None,
        },
    )


@app.get("/properties/{property_id}/units/new", response_class=HTMLResponse)
async def unit_new_form(
    request: Request,
    property_id: int,
    property_name: str | None = Query(default=None),
):
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "unit_form.html",
        {
            "request": request,
            "property_id": property_id,
            "property_name": property_name,
            "error": None,
        },
    )


@app.post("/properties/{property_id}/units/new", response_class=HTMLResponse)
async def unit_create(
    request: Request,
    property_id: int,
    area: float = Form(...),
    floor: int | None = Form(None),
    status: str = Form("AVAILABLE"),
    monthly_rent: float = Form(...),
):
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login")

    headers = {"Authorization": f"Bearer {token}"}

    # 1) Получаем существующие помещения объекта, чтобы придумать следующий номер
    async with httpx.AsyncClient() as client:
        try:
            resp_units = await client.get(
                f"{PROPERTY_BASE}/api/v1/units/",
                headers=headers,
                params={"property_id": property_id},
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "unit_form.html",
                {
                    "request": request,
                    "property_id": property_id,
                    "error": "Не удалось получить список помещений (service down)",
                },
                status_code=503,
            )

    unit_number = "1"
    if resp_units.status_code in (200, 201):
        try:
            units = resp_units.json()
            existing_numbers = []
            for u in units:
                num = u.get("unit_number")
                # на случай, если это строка
                try:
                    existing_numbers.append(int(num))
                except (TypeError, ValueError):
                    pass
            if existing_numbers:
                unit_number = str(max(existing_numbers) + 1)
        except Exception:
            # если что-то пошло не так при разборе, оставим "1"
            unit_number = "1"

    json_data = {
        "property_id": property_id,
        "unit_number": unit_number,
        "area": area,
        "floor": floor,
        "status": status,
        "monthly_rent": monthly_rent,
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{PROPERTY_BASE}/api/v1/units/",
                headers=headers,
                json=json_data,
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "unit_form.html",
                {
                    "request": request,
                    "property_id": property_id,
                    "error": "Сервис помещений недоступен",
                },
                status_code=503,
            )

    if resp.status_code not in (200, 201):
        return templates.TemplateResponse(
            "unit_form.html",
            {
                "request": request,
                "property_id": property_id,
                "error": f"Ошибка создания помещения: {resp.status_code} {resp.text}",
            },
            status_code=resp.status_code,
        )

    return RedirectResponse(
        url=f"/properties/{property_id}/units",
        status_code=303,
    )


@app.get("/leases/new", response_class=HTMLResponse)
async def lease_new_form(
    request: Request,
    unit_id: int = Query(...),
    property_id: int = Query(...),
    property_name: str | None = Query(default=None),
):
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "lease_form.html",
        {
            "request": request,
            "unit_id": unit_id,
            "property_id": property_id,
            "property_name": property_name,
            "error": None,
        },
    )




@app.post("/leases/new", response_class=HTMLResponse)
async def lease_create(
    request: Request,
    unit_id: int = Form(...),
    property_id: int = Form(...),
    tenant_id: int = Form(...),
    start_date: str = Form(...),
    end_date: str | None = Form(None),
    monthly_rent: float = Form(...),
    status: str = Form("ACTIVE"),
):
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login")

    headers = {"Authorization": f"Bearer {token}"}
    json_data = {
        "unit_id": unit_id,
        "tenant_id": tenant_id,
        "start_date": start_date,
        "end_date": end_date,
        "monthly_rent": monthly_rent,
        "status": status,
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{LEASING_BASE}/api/v1/leases/",
                headers=headers,
                json=json_data,
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "lease_form.html",
                {
                    "request": request,
                    "unit_id": unit_id,
                    "property_id": property_id,
                    "property_name": None,
                    "error": "Сервис договоров недоступен",
                },
                status_code=503,
            )

    if resp.status_code not in (200, 201):
        return templates.TemplateResponse(
            "lease_form.html",
            {
                "request": request,
                "unit_id": unit_id,
                "property_id": property_id,
                "property_name": None,
                "error": f"Ошибка создания договора: {resp.status_code} {resp.text}",
            },
            status_code=resp.status_code,
        )

    # после успешного создания → назад к помещениям этого объекта
    return RedirectResponse(
        url=f"/properties/{property_id}/units",
        status_code=303,
    )
