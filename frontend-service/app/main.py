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
    return RedirectResponse(url="/catalog")


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, redirect: str | None = Query(None)):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None, "redirect": redirect},
    )


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    redirect: str | None = Form(None),
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

    redirect_url = redirect if redirect else "/properties"
    response = RedirectResponse(url=redirect_url, status_code=303)
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

    headers = {"Authorization": f"Bearer {token}"}
    json_data = {
        "name": name,
        "address": address,
        "description": description if description else None,
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


@app.get("/leases", response_class=HTMLResponse)
async def leases_list(request: Request):
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login?redirect=/leases")

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{LEASING_BASE}/api/v1/leases/",
                headers=headers,
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "leases.html",
                {
                    "request": request,
                    "leases": [],
                    "error": "Сервис договоров недоступен",
                },
                status_code=503,
            )

        if resp.status_code == 401:
            response = RedirectResponse(url="/login?redirect=/leases", status_code=303)
            response.delete_cookie("access_token")
            return response

        if resp.status_code not in (200, 201):
            return templates.TemplateResponse(
                "leases.html",
                {
                    "request": request,
                    "leases": [],
                    "error": f"Ошибка сервиса договоров: {resp.status_code}",
                },
                status_code=resp.status_code,
            )

        leases = resp.json()
        unit_cache: dict[int, dict | None] = {}
        property_cache: dict[int, dict | None] = {}
        leases_with_details = []

        for lease in leases:
            unit_id = lease.get("unit_id")
            unit_info = unit_cache.get(unit_id)

            if unit_info is None and unit_id is not None:
                try:
                    unit_resp = await client.get(
                        f"{PROPERTY_BASE}/api/v1/units/public/{unit_id}",
                        timeout=10.0,
                    )
                    if unit_resp.status_code == 200:
                        unit_info = unit_resp.json()
                    else:
                        unit_info = None
                except httpx.RequestError:
                    unit_info = None

                unit_cache[unit_id] = unit_info

            property_info = None
            if unit_info:
                property_id = unit_info.get("property_id")
                property_info = property_cache.get(property_id)

                if property_info is None and property_id is not None:
                    try:
                        property_resp = await client.get(
                            f"{PROPERTY_BASE}/api/v1/properties/{property_id}",
                            timeout=10.0,
                        )
                        if property_resp.status_code == 200:
                            property_info = property_resp.json()
                        else:
                            property_info = None
                    except httpx.RequestError:
                        property_info = None

                    property_cache[property_id] = property_info

            leases_with_details.append(
                {
                    "lease": lease,
                    "unit": unit_info,
                    "property": property_info,
                }
            )

    return templates.TemplateResponse(
        "leases.html",
        {
            "request": request,
            "leases": leases_with_details,
            "error": None,
        },
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

    return RedirectResponse(
        url=f"/catalog/{property_id}",
        status_code=303,
    )


# Публичный каталог объектов
@app.get("/catalog", response_class=HTMLResponse)
async def catalog_list(
    request: Request,
    name: str | None = Query(None),
    address: str | None = Query(None),
):
    """Публичный каталог всех объектов с фильтрацией"""
    params = {}
    if name:
        params["name"] = name
    if address:
        params["address"] = address
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{PROPERTY_BASE}/api/v1/properties/public",
                params=params,
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "catalog.html",
                {
                    "request": request,
                    "properties": [],
                    "error": "Сервис объектов недоступен",
                    "name": name or "",
                    "address": address or "",
                },
                status_code=503,
            )
    
    if resp.status_code not in (200, 201):
        return templates.TemplateResponse(
            "catalog.html",
            {
                "request": request,
                "properties": [],
                "error": f"Ошибка сервиса объектов: {resp.status_code}",
                "name": name or "",
                "address": address or "",
            },
            status_code=resp.status_code,
        )
    
    properties = resp.json()
    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "properties": properties,
            "error": None,
            "name": name or "",
            "address": address or "",
        },
    )


@app.get("/catalog/{property_id}", response_class=HTMLResponse)
async def catalog_property_detail(
    request: Request,
    property_id: int,
):
    """Публичная страница объекта с помещениями"""
    async with httpx.AsyncClient() as client:
        # Получаем информацию об объекте
        try:
            resp_property = await client.get(
                f"{PROPERTY_BASE}/api/v1/properties/{property_id}",
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "catalog_detail.html",
                {
                    "request": request,
                    "property": None,
                    "units": [],
                    "error": "Сервис объектов недоступен",
                },
                status_code=503,
            )
        
        if resp_property.status_code != 200:
            return templates.TemplateResponse(
                "catalog_detail.html",
                {
                    "request": request,
                    "property": None,
                    "units": [],
                    "error": f"Объект не найден: {resp_property.status_code}",
                },
                status_code=resp_property.status_code,
            )
        
        property_data = resp_property.json()
        
        # Получаем помещения объекта
        try:
            resp_units = await client.get(
                f"{PROPERTY_BASE}/api/v1/units/public",
                params={"property_id": property_id},
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "catalog_detail.html",
                {
                    "request": request,
                    "property": property_data,
                    "units": [],
                    "error": "Сервис помещений недоступен",
                },
                status_code=503,
            )
        
        units = resp_units.json() if resp_units.status_code == 200 else []
        
        return templates.TemplateResponse(
            "catalog_detail.html",
            {
                "request": request,
                "property": property_data,
                "units": units,
                "error": None,
            },
        )


@app.get("/catalog/{property_id}/unit/{unit_id}/lease", response_class=HTMLResponse)
async def catalog_unit_lease_form(
    request: Request,
    property_id: int,
    unit_id: int,
):
    """Форма создания договора для публичного каталога"""
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url=f"/login?redirect=/catalog/{property_id}/unit/{unit_id}/lease")
    
    # Получаем информацию о помещении
    async with httpx.AsyncClient() as client:
        try:
            resp_unit = await client.get(
                f"{PROPERTY_BASE}/api/v1/units/public/{unit_id}",
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "catalog_lease_form.html",
                {
                    "request": request,
                    "unit": None,
                    "property_id": property_id,
                    "error": "Сервис помещений недоступен",
                },
                status_code=503,
            )
        
        if resp_unit.status_code != 200:
            return templates.TemplateResponse(
                "catalog_lease_form.html",
                {
                    "request": request,
                    "unit": None,
                    "property_id": property_id,
                    "error": "Помещение не найдено",
                },
                status_code=resp_unit.status_code,
            )
        
        unit = resp_unit.json()
        
        return templates.TemplateResponse(
            "catalog_lease_form.html",
            {
                "request": request,
                "unit": unit,
                "property_id": property_id,
                "error": None,
            },
        )


@app.post("/catalog/{property_id}/unit/{unit_id}/lease", response_class=HTMLResponse)
async def catalog_unit_lease_create(
    request: Request,
    property_id: int,
    unit_id: int,
    start_date: str = Form(...),
    end_date: str | None = Form(None),
    status: str = Form("ACTIVE"),
):
    """Создание договора из публичного каталога"""
    token = get_token_from_cookies(request)
    if not token:
        return RedirectResponse(url="/login")
    
    # Получаем информацию о помещении для цены
    async with httpx.AsyncClient() as client:
        try:
            resp_unit = await client.get(
                f"{PROPERTY_BASE}/api/v1/units/public/{unit_id}",
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "catalog_lease_form.html",
                {
                    "request": request,
                    "unit": None,
                    "property_id": property_id,
                    "error": "Сервис помещений недоступен",
                },
                status_code=503,
            )
        
        if resp_unit.status_code != 200:
            return templates.TemplateResponse(
                "catalog_lease_form.html",
                {
                    "request": request,
                    "unit": None,
                    "property_id": property_id,
                    "error": "Помещение не найдено",
                },
                status_code=resp_unit.status_code,
            )
        
        unit = resp_unit.json()
        monthly_rent = float(unit["monthly_rent"])
        
        headers = {"Authorization": f"Bearer {token}"}
        json_data = {
            "unit_id": unit_id,
            "start_date": start_date,
            "end_date": end_date,
            "monthly_rent": monthly_rent,  # Берем цену из помещения
            "status": status,
        }
        
        try:
            resp = await client.post(
                f"{LEASING_BASE}/api/v1/leases/",
                headers=headers,
                json=json_data,
                timeout=10.0,
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                "catalog_lease_form.html",
                {
                    "request": request,
                    "unit": unit,
                    "property_id": property_id,
                    "error": "Сервис договоров недоступен",
                },
                status_code=503,
            )
        
        if resp.status_code not in (200, 201):
            return templates.TemplateResponse(
                "catalog_lease_form.html",
                {
                    "request": request,
                    "unit": unit,
                    "property_id": property_id,
                    "error": f"Ошибка создания договора: {resp.status_code} {resp.text}",
                },
                status_code=resp.status_code,
            )
        
        return RedirectResponse(
            url=f"/catalog/{property_id}",
            status_code=303,
        )


@app.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "error": None,
            "success": None,
            "email": "",
            "username": "",
            "password": "",
            "confirm_password": "",
        },
    )


@app.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    # локальная проверка совпадения паролей
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Пароль и подтверждение пароля не совпадают.",
                "success": None,
                "email": email,
                "username": username,
                "password": password,
                "confirm_password": confirm_password,
            },
            status_code=400,
        )

    try:
        async with httpx.AsyncClient(base_url=AUTH_BASE, timeout=5.0) as client:
            payload = {
                "email": email,
                "username": username,
                "password": password,
            }
            resp = await client.post("/api/v1/auth/register", json=payload)

        if resp.status_code in (200, 201):
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": None,
                    "success": "Аккаунт успешно создан. Теперь вы можете войти.",
                    "email": email,
                    "username": username,
                    "password": password,
                    "confirm_password": confirm_password,
                },
            )

        # ошибка от auth-сервиса
        try:
            data = resp.json()
        except Exception:
            data = {}

        backend_error = data.get("detail") or data.get("message") or "Ошибка регистрации."

        if resp.status_code in (400, 409) and "email" in str(backend_error).lower():
            backend_error = "Аккаунт с таким email уже зарегистрирован."

        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": backend_error,
                "success": None,
                "email": email,
                "username": username,
                "password": password,
                "confirm_password": confirm_password,
            },
            status_code=resp.status_code,
        )

    except httpx.RequestError:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Сервис аутентификации временно недоступен. Попробуйте позже.",
                "success": None,
                "email": email,
                "username": username,
                "password": password,
                "confirm_password": confirm_password,
            },
            status_code=503,
        )
