from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Optional
import requests
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.config import SPEERO_API_URL, SPEERO_API_KEY
from backend.database import Base, engine, SessionLocal, get_db, IS_POSTGRES, ACTIVE_DATABASE_URL
from backend.models import (
    Persona,
    Rol,
    Estado,
    Usuario,
    Vehiculo,
    Consulta,
    Producto,
    Inventario,
    Facturacion,
    Kardex,
    SolicitudRepuesto,
)
from backend.schemas import (
    LoginRequest,
    TokenUserResponse,
    RolResponse,
    EstadoResponse,
    PersonaCreate,
    PersonaUpdate,
    PersonaResponse,
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    VehiculoCreate,
    VehiculoUpdate,
    VehiculoResponse,
    ConsultaCreate,
    ConsultaUpdate,
    ConsultaResponse,
    ProductoCompraCreate,
    ProductoCatalogoResponse,
    InventarioLoteResponse,
    SolicitudRepuestoCreate,
    SolicitudRepuestoResponse,
    KardexItemResponse,
    FacturaDetalleResponse,
)
from backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_roles,
)

app = FastAPI(
    title="Taller Pro - Sistema de Gestión Automotriz",
    description="API Backend para Diagnóstico, Reparación, Bodega/Kardex y Facturación",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# INICIALIZACIÓN DE BASE DE DATOS Y DATOS SEMILLA
# =============================================================================
def init_db_and_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Rol).count() == 0:
            roles_seed = [
                Rol(id_rol=1, nombre="Administrador", descripcion_corta="Acceso total a todos los módulos del sistema"),
                Rol(id_rol=2, nombre="Mecanico", descripcion_corta="Acceso a consultas, vehículos y solicitud de productos a bodega"),
                Rol(id_rol=3, nombre="Recepcionista", descripcion_corta="Acceso a facturación, personas, consultas y vehículos"),
                Rol(id_rol=4, nombre="Bodeguero", descripcion_corta="Acceso a productos (API/Manual), compras, inventario y despachos"),
            ]
            db.add_all(roles_seed)
            db.flush()

        if db.query(Estado).count() == 0:
            estados_seed = [
                Estado(id_estado=1, nombre="Activo"),
                Estado(id_estado=2, nombre="Inactivo"),
                Estado(id_estado=3, nombre="Pendiente"),
                Estado(id_estado=4, nombre="En Diagnostico"),
                Estado(id_estado=5, nombre="En Reparacion"),
                Estado(id_estado=6, nombre="Finalizado"),
                Estado(id_estado=7, nombre="Despachado"),
                Estado(id_estado=8, nombre="Rechazado"),
            ]
            db.add_all(estados_seed)
            db.flush()

        if db.query(Persona).count() == 0:
            personas_seed = [
                Persona(id_persona=1, nombre="Carlos Mendoza", telefono="5551-0100", email="admin@tallerpro.com", edad=38, sexo="M", nit="10020030-1"),
                Persona(id_persona=2, nombre="Roberto Gómez", telefono="5551-0101", email="rgomez@tallerpro.com", edad=34, sexo="M", nit="20030040-2"),
                Persona(id_persona=3, nombre="Laura Castillo", telefono="5551-0102", email="lcastillo@tallerpro.com", edad=29, sexo="F", nit="30040050-3"),
                Persona(id_persona=4, nombre="Miguel Ángel Pérez", telefono="5551-0103", email="mperez@tallerpro.com", edad=31, sexo="M", nit="40050060-4"),
                Persona(id_persona=5, nombre="Alejandro Morales", telefono="5559-8877", email="amorales@correo.com", edad=42, sexo="M", nit="78945612-K"),
                Persona(id_persona=6, nombre="Sofía Herrera", telefono="5554-3322", email="sherrera@correo.com", edad=35, sexo="F", nit="45612389-5"),
            ]
            db.add_all(personas_seed)
            db.flush()

        if db.query(Usuario).count() == 0:
            default_pw = hash_password("admin123")
            usuarios_seed = [
                Usuario(id_usuario=1, id_rol=1, id_persona=1, id_estado=1, alias="admin", contrasenia=default_pw),
                Usuario(id_usuario=2, id_rol=2, id_persona=2, id_estado=1, alias="mecanico", contrasenia=default_pw),
                Usuario(id_usuario=3, id_rol=3, id_persona=3, id_estado=1, alias="recepcion", contrasenia=default_pw),
                Usuario(id_usuario=4, id_rol=4, id_persona=4, id_estado=1, alias="bodega", contrasenia=default_pw),
            ]
            db.add_all(usuarios_seed)
            db.flush()

        if db.query(Vehiculo).count() == 0:
            vehiculos_seed = [
                Vehiculo(id_vehiculo=1, id_persona=5, vin="JTDBE32K900128931", placa="P-482KLM"),
                Vehiculo(id_vehiculo=2, id_persona=6, vin="1HGCM82633A004352", placa="P-910XYZ"),
            ]
            db.add_all(vehiculos_seed)
            db.flush()

        if db.query(Producto).count() == 0:
            productos_seed = [
                Producto(
                    id_producto=1,
                    nombre="Juego Pastillas de Freno Cerámicas Delanteras",
                    url_imagen="https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&w=400&q=80",
                ),
                Producto(
                    id_producto=2,
                    nombre="Filtro de Aceite Sintético Alto Flujo OEM",
                    url_imagen="https://images.unsplash.com/photo-1635784063388-1ff609e12d7c?auto=format&fit=crop&w=400&q=80",
                ),
                Producto(
                    id_producto=3,
                    nombre="Bujía Iridium IX Encendido Avanzado",
                    url_imagen="https://images.unsplash.com/photo-1580273916550-e323be2ae537?auto=format&fit=crop&w=400&q=80",
                ),
                Producto(
                    id_producto=4,
                    nombre="Kit Embrague Hidráulico Completo 225mm",
                    url_imagen="https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?auto=format&fit=crop&w=400&q=80",
                ),
            ]
            db.add_all(productos_seed)
            db.flush()

            now = datetime.now()
            inventario_seed = [
                Inventario(id_producto=1, costo_compra=Decimal("280.00"), costo_venta=Decimal("336.00"), fecha_compra=now - timedelta(days=5), cantidad=14),
                Inventario(id_producto=2, costo_compra=Decimal("65.00"), costo_venta=Decimal("78.00"), fecha_compra=now - timedelta(days=4), cantidad=25),
                Inventario(id_producto=3, costo_compra=Decimal("55.00"), costo_venta=Decimal("66.00"), fecha_compra=now - timedelta(days=3), cantidad=40),
                Inventario(id_producto=4, costo_compra=Decimal("950.00"), costo_venta=Decimal("1140.00"), fecha_compra=now - timedelta(days=2), cantidad=5),
            ]
            db.add_all(inventario_seed)
            db.flush()

        if db.query(Consulta).count() == 0:
            now = datetime.now()
            consultas_seed = [
                Consulta(
                    id_consulta=1,
                    id_vehiculo=1,
                    id_usuario=2,
                    id_estado=5,
                    detalle_consulta="Ruido metálico al frenar a baja velocidad y vibración en el pedal.",
                    detalle_diagnostico="Desgaste severo en pastillas delanteras (menos de 2mm). Se requiere reemplazo de juego delantero.",
                    fecha_ingreso=now - timedelta(days=1),
                    fecha_salida=None,
                ),
                Consulta(
                    id_consulta=2,
                    id_vehiculo=2,
                    id_usuario=2,
                    id_estado=4,
                    detalle_consulta="Mantenimiento preventivo de 40,000 km y revisión de encendido en frío.",
                    detalle_diagnostico="Pendiente prueba de compresión y cambio de filtro/bujías.",
                    fecha_ingreso=now - timedelta(hours=3),
                    fecha_salida=None,
                ),
            ]
            db.add_all(consultas_seed)
            db.flush()

            factura_1 = Facturacion(id_factura=1, id_consulta=1)
            db.add(factura_1)
            db.flush()

            # Kardex de ejemplo ya despachado en consulta 1 + una solicitud pendiente para el bodeguero
            kardex_1 = Kardex(
                id_factura=1,
                id_producto=1,
                cantidad=1,
                sub_total=Decimal("336.00"),
            )
            db.add(kardex_1)

            solicitud_seed_despachada = SolicitudRepuesto(
                id_consulta=1,
                id_producto=1,
                id_usuario_solicitante=2,
                id_usuario_despachador=4,
                id_estado=7,  # Despachado
                cantidad=1,
                fecha_solicitud=now - timedelta(hours=18),
                fecha_despacho=now - timedelta(hours=16),
            )
            solicitud_seed_pendiente = SolicitudRepuesto(
                id_consulta=2,
                id_producto=2,
                id_usuario_solicitante=2,
                id_usuario_despachador=None,
                id_estado=3,  # Pendiente
                cantidad=1,
                fecha_solicitud=now - timedelta(hours=1),
                fecha_despacho=None,
            )
            db.add_all([solicitud_seed_despachada, solicitud_seed_pendiente])

        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db_and_seed()


# =============================================================================
# HELPERS DE SERIALIZACIÓN
# =============================================================================
def _build_consulta_response(c: Consulta) -> ConsultaResponse:
    return ConsultaResponse(
        id_consulta=c.id_consulta,
        id_vehiculo=c.id_vehiculo,
        vehiculo_placa=c.vehiculo.placa if c.vehiculo else "N/A",
        vehiculo_vin=c.vehiculo.vin if c.vehiculo else "N/A",
        propietario_nombre=c.vehiculo.propietario.nombre if (c.vehiculo and c.vehiculo.propietario) else "N/A",
        id_usuario=c.id_usuario,
        mecanico_nombre=c.mecanico.persona.nombre if (c.mecanico and c.mecanico.persona) else "N/A",
        mecanico_alias=c.mecanico.alias if c.mecanico else "N/A",
        id_estado=c.id_estado,
        estado_nombre=c.estado.nombre if c.estado else "N/A",
        detalle_consulta=c.detalle_consulta,
        detalle_diagnostico=c.detalle_diagnostico,
        fecha_ingreso=c.fecha_ingreso,
        fecha_salida=c.fecha_salida,
        id_factura=c.factura.id_factura if c.factura else None,
    )


def _get_producto_stats(db: Session, id_producto: int):
    lotes = (
        db.query(Inventario)
        .filter(Inventario.id_producto == id_producto)
        .order_by(Inventario.fecha_compra.desc(), Inventario.id_inventario.desc())
        .all()
    )
    stock_total = sum(l.cantidad for l in lotes)
    ultimo_lote = lotes[0] if lotes else None
    ultimo_costo_compra = float(ultimo_lote.costo_compra) if ultimo_lote else 0.0
    precio_venta_actual = float(ultimo_lote.costo_venta) if ultimo_lote else 0.0
    return stock_total, ultimo_costo_compra, precio_venta_actual


# =============================================================================
# 1. ENDPOINTS DE AUTENTICACIÓN
# =============================================================================
@app.post("/api/auth/login", response_model=TokenUserResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(func.lower(Usuario.alias) == payload.alias.strip().lower()).first()
    if not user or not verify_password(payload.contrasenia, user.contrasenia):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verifica tu alias y contraseña.",
        )

    if user.estado and user.estado.nombre.lower() != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este usuario se encuentra inactivo.",
        )

    token = create_access_token(
        user_id=user.id_usuario,
        alias=user.alias,
        rol_nombre=user.rol.nombre if user.rol else "",
    )
    user.token = token
    db.commit()
    db.refresh(user)

    return TokenUserResponse(
        id_usuario=user.id_usuario,
        alias=user.alias,
        id_rol=user.id_rol,
        rol_nombre=user.rol.nombre if user.rol else "",
        id_persona=user.id_persona,
        persona_nombre=user.persona.nombre if user.persona else user.alias,
        id_estado=user.id_estado,
        estado_nombre=user.estado.nombre if user.estado else "Activo",
        token=token,
    )


@app.post("/api/auth/logout")
def logout(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.token = None
    db.commit()
    return {"message": "Sesión cerrada correctamente."}


@app.get("/api/auth/me", response_model=TokenUserResponse)
def get_me(current_user: Usuario = Depends(get_current_user)):
    return TokenUserResponse(
        id_usuario=current_user.id_usuario,
        alias=current_user.alias,
        id_rol=current_user.id_rol,
        rol_nombre=current_user.rol.nombre if current_user.rol else "",
        id_persona=current_user.id_persona,
        persona_nombre=current_user.persona.nombre if current_user.persona else current_user.alias,
        id_estado=current_user.id_estado,
        estado_nombre=current_user.estado.nombre if current_user.estado else "Activo",
        token=current_user.token or "",
    )


# =============================================================================
# 2. CATÁLOGOS BASE Y RESUMEN OPERATIVO
# =============================================================================
@app.get("/api/roles", response_model=List[RolResponse])
def listar_roles(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Rol).order_by(Rol.id_rol.asc()).all()


@app.get("/api/estados", response_model=List[EstadoResponse])
def listar_estados(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Estado).order_by(Estado.id_estado.asc()).all()


@app.get("/api/dashboard/resumen")
def obtener_resumen(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    total_vehiculos = db.query(Vehiculo).count()
    consultas_activas = (
        db.query(Consulta)
        .join(Estado, Consulta.id_estado == Estado.id_estado)
        .filter(func.lower(Estado.nombre).in_(["pendiente", "en diagnostico", "en reparacion"]))
        .count()
    )
    solicitudes_pendientes = (
        db.query(SolicitudRepuesto)
        .join(Estado, SolicitudRepuesto.id_estado == Estado.id_estado)
        .filter(func.lower(Estado.nombre) == "pendiente")
        .count()
    )
    unidades_inventario = db.query(func.coalesce(func.sum(Inventario.cantidad), 0)).scalar() or 0
    total_facturado = db.query(func.coalesce(func.sum(Kardex.sub_total), 0)).scalar() or 0

    return {
        "total_vehiculos": total_vehiculos,
        "consultas_activas": consultas_activas,
        "solicitudes_pendientes": solicitudes_pendientes,
        "unidades_inventario": int(unidades_inventario),
        "total_facturado": float(total_facturado),
        "motor_bd": "PostgreSQL" if IS_POSTGRES else "SQLite (Modo Local)",
    }


# =============================================================================
# 3. MÓDULO DE PERSONAS (Administrador, Recepcionista)
# =============================================================================
@app.get("/api/personas", response_model=List[PersonaResponse])
def listar_personas(
    q: Optional[str] = Query(default=None),
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista", "Mecanico")),
    db: Session = Depends(get_db),
):
    query = db.query(Persona)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            (Persona.nombre.ilike(pattern))
            | (Persona.nit.ilike(pattern))
            | (Persona.email.ilike(pattern))
        )
    return query.order_by(Persona.id_persona.desc()).all()


@app.post("/api/personas", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
def crear_persona(
    payload: PersonaCreate,
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista")),
    db: Session = Depends(get_db),
):
    existente_nit = db.query(Persona).filter(func.lower(Persona.nit) == payload.nit.strip().lower()).first()
    if existente_nit:
        raise HTTPException(status_code=400, detail=f"Ya existe una persona registrada con el NIT {payload.nit}.")

    if payload.email:
        existente_email = db.query(Persona).filter(func.lower(Persona.email) == payload.email.strip().lower()).first()
        if existente_email:
            raise HTTPException(status_code=400, detail=f"Ya existe una persona con el correo {payload.email}.")

    nueva = Persona(
        nombre=payload.nombre.strip(),
        telefono=payload.telefono.strip() if payload.telefono else None,
        email=payload.email.strip() if payload.email else None,
        edad=payload.edad,
        sexo=payload.sexo,
        nit=payload.nit.strip(),
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@app.put("/api/personas/{id_persona}", response_model=PersonaResponse)
def actualizar_persona(
    id_persona: int,
    payload: PersonaUpdate,
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista")),
    db: Session = Depends(get_db),
):
    persona = db.query(Persona).filter(Persona.id_persona == id_persona).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada.")

    if payload.nombre is not None:
        persona.nombre = payload.nombre.strip()
    if payload.telefono is not None:
        persona.telefono = payload.telefono.strip()
    if payload.email is not None:
        persona.email = payload.email.strip() or None
    if payload.edad is not None:
        persona.edad = payload.edad
    if payload.sexo is not None:
        persona.sexo = payload.sexo
    if payload.nit is not None:
        persona.nit = payload.nit.strip()

    db.commit()
    db.refresh(persona)
    return persona


# =============================================================================
# 4. MÓDULO DE USUARIOS (Administrador + listado de mecánicos para Recepción)
# =============================================================================
@app.get("/api/usuarios", response_model=List[UsuarioResponse])
def listar_usuarios(
    current_user: Usuario = Depends(require_roles("Administrador")),
    db: Session = Depends(get_db),
):
    usuarios = db.query(Usuario).order_by(Usuario.id_usuario.asc()).all()
    return [
        UsuarioResponse(
            id_usuario=u.id_usuario,
            id_rol=u.id_rol,
            rol_nombre=u.rol.nombre if u.rol else "",
            id_persona=u.id_persona,
            persona_nombre=u.persona.nombre if u.persona else "",
            id_estado=u.id_estado,
            estado_nombre=u.estado.nombre if u.estado else "",
            alias=u.alias,
        )
        for u in usuarios
    ]


@app.get("/api/usuarios/mecanicos", response_model=List[UsuarioResponse])
def listar_mecanicos(
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista", "Mecanico")),
    db: Session = Depends(get_db),
):
    mecanicos = (
        db.query(Usuario)
        .join(Rol, Usuario.id_rol == Rol.id_rol)
        .join(Estado, Usuario.id_estado == Estado.id_estado)
        .filter(func.lower(Rol.nombre).in_(["mecanico", "mecánico"]))
        .filter(func.lower(Estado.nombre) == "activo")
        .order_by(Usuario.id_usuario.asc())
        .all()
    )
    return [
        UsuarioResponse(
            id_usuario=u.id_usuario,
            id_rol=u.id_rol,
            rol_nombre=u.rol.nombre if u.rol else "Mecanico",
            id_persona=u.id_persona,
            persona_nombre=u.persona.nombre if u.persona else u.alias,
            id_estado=u.id_estado,
            estado_nombre=u.estado.nombre if u.estado else "Activo",
            alias=u.alias,
        )
        for u in mecanicos
    ]


@app.post("/api/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    payload: UsuarioCreate,
    current_user: Usuario = Depends(require_roles("Administrador")),
    db: Session = Depends(get_db),
):
    existente = db.query(Usuario).filter(func.lower(Usuario.alias) == payload.alias.strip().lower()).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"El alias '{payload.alias}' ya está en uso.")

    persona = db.query(Persona).filter(Persona.id_persona == payload.id_persona).first()
    if not persona:
        raise HTTPException(status_code=404, detail="La persona seleccionada no existe.")

    rol = db.query(Rol).filter(Rol.id_rol == payload.id_rol).first()
    if not rol:
        raise HTTPException(status_code=404, detail="El rol seleccionado no existe.")

    nuevo = Usuario(
        id_rol=payload.id_rol,
        id_persona=payload.id_persona,
        id_estado=payload.id_estado,
        alias=payload.alias.strip(),
        contrasenia=hash_password(payload.contrasenia),
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return UsuarioResponse(
        id_usuario=nuevo.id_usuario,
        id_rol=nuevo.id_rol,
        rol_nombre=nuevo.rol.nombre if nuevo.rol else "",
        id_persona=nuevo.id_persona,
        persona_nombre=nuevo.persona.nombre if nuevo.persona else "",
        id_estado=nuevo.id_estado,
        estado_nombre=nuevo.estado.nombre if nuevo.estado else "",
        alias=nuevo.alias,
    )


@app.put("/api/usuarios/{id_usuario}", response_model=UsuarioResponse)
def actualizar_usuario(
    id_usuario: int,
    payload: UsuarioUpdate,
    current_user: Usuario = Depends(require_roles("Administrador")),
    db: Session = Depends(get_db),
):
    u = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if payload.id_rol is not None:
        u.id_rol = payload.id_rol
    if payload.id_persona is not None:
        u.id_persona = payload.id_persona
    if payload.id_estado is not None:
        u.id_estado = payload.id_estado
    if payload.alias is not None:
        u.alias = payload.alias.strip()
    if payload.contrasenia:
        u.contrasenia = hash_password(payload.contrasenia)
        u.token = None

    db.commit()
    db.refresh(u)

    return UsuarioResponse(
        id_usuario=u.id_usuario,
        id_rol=u.id_rol,
        rol_nombre=u.rol.nombre if u.rol else "",
        id_persona=u.id_persona,
        persona_nombre=u.persona.nombre if u.persona else "",
        id_estado=u.id_estado,
        estado_nombre=u.estado.nombre if u.estado else "",
        alias=u.alias,
    )


# =============================================================================
# 5. MÓDULO DE VEHÍCULOS (Administrador, Recepcionista, Mecánico)
# =============================================================================
@app.get("/api/vehiculos", response_model=List[VehiculoResponse])
def listar_vehiculos(
    q: Optional[str] = Query(default=None),
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista", "Mecanico")),
    db: Session = Depends(get_db),
):
    query = db.query(Vehiculo).join(Persona, Vehiculo.id_persona == Persona.id_persona)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            (Vehiculo.placa.ilike(pattern))
            | (Vehiculo.vin.ilike(pattern))
            | (Persona.nombre.ilike(pattern))
        )
    vehiculos = query.order_by(Vehiculo.id_vehiculo.desc()).all()
    return [
        VehiculoResponse(
            id_vehiculo=v.id_vehiculo,
            id_persona=v.id_persona,
            propietario_nombre=v.propietario.nombre if v.propietario else "Sin propietario",
            propietario_nit=v.propietario.nit if v.propietario else "N/A",
            vin=v.vin,
            placa=v.placa,
        )
        for v in vehiculos
    ]


@app.post("/api/vehiculos", response_model=VehiculoResponse, status_code=status.HTTP_201_CREATED)
def crear_vehiculo(
    payload: VehiculoCreate,
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista")),
    db: Session = Depends(get_db),
):
    persona = db.query(Persona).filter(Persona.id_persona == payload.id_persona).first()
    if not persona:
        raise HTTPException(status_code=404, detail="El propietario (persona) seleccionado no existe.")

    vin_clean = payload.vin.strip().upper()
    placa_clean = payload.placa.strip().upper()

    if db.query(Vehiculo).filter(func.upper(Vehiculo.vin) == vin_clean).first():
        raise HTTPException(status_code=400, detail=f"Ya existe un vehículo con el VIN {vin_clean}.")

    if db.query(Vehiculo).filter(func.upper(Vehiculo.placa) == placa_clean).first():
        raise HTTPException(status_code=400, detail=f"Ya existe un vehículo con la placa {placa_clean}.")

    nuevo = Vehiculo(
        id_persona=payload.id_persona,
        vin=vin_clean,
        placa=placa_clean,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return VehiculoResponse(
        id_vehiculo=nuevo.id_vehiculo,
        id_persona=nuevo.id_persona,
        propietario_nombre=nuevo.propietario.nombre if nuevo.propietario else "",
        propietario_nit=nuevo.propietario.nit if nuevo.propietario else "",
        vin=nuevo.vin,
        placa=nuevo.placa,
    )


@app.put("/api/vehiculos/{id_vehiculo}", response_model=VehiculoResponse)
def actualizar_vehiculo(
    id_vehiculo: int,
    payload: VehiculoUpdate,
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista")),
    db: Session = Depends(get_db),
):
    v = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == id_vehiculo).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado.")

    if payload.id_persona is not None:
        v.id_persona = payload.id_persona
    if payload.vin is not None:
        v.vin = payload.vin.strip().upper()
    if payload.placa is not None:
        v.placa = payload.placa.strip().upper()

    db.commit()
    db.refresh(v)
    return VehiculoResponse(
        id_vehiculo=v.id_vehiculo,
        id_persona=v.id_persona,
        propietario_nombre=v.propietario.nombre if v.propietario else "",
        propietario_nit=v.propietario.nit if v.propietario else "",
        vin=v.vin,
        placa=v.placa,
    )


# =============================================================================
# 6. MÓDULO DE CONSULTAS (Administrador, Recepcionista, Mecánico)
# =============================================================================
@app.get("/api/consultas", response_model=List[ConsultaResponse])
def listar_consultas(
    id_estado: Optional[int] = Query(default=None),
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista", "Mecanico")),
    db: Session = Depends(get_db),
):
    query = db.query(Consulta)
    if id_estado is not None:
        query = query.filter(Consulta.id_estado == id_estado)

    consultas = query.order_by(Consulta.fecha_ingreso.desc(), Consulta.id_consulta.desc()).all()
    return [_build_consulta_response(c) for c in consultas]


@app.post("/api/consultas", response_model=ConsultaResponse, status_code=status.HTTP_201_CREATED)
def crear_consulta(
    payload: ConsultaCreate,
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista", "Mecanico")),
    db: Session = Depends(get_db),
):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == payload.id_vehiculo).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="El vehículo indicado no existe.")

    mecanico = db.query(Usuario).filter(Usuario.id_usuario == payload.id_usuario).first()
    if not mecanico or not mecanico.rol or mecanico.rol.nombre.lower() not in ("mecanico", "mecánico"):
        raise HTTPException(
            status_code=400,
            detail="El usuario asignado a la consulta debe tener estrictamente el rol de Mecánico.",
        )

    nueva = Consulta(
        id_vehiculo=payload.id_vehiculo,
        id_usuario=payload.id_usuario,
        id_estado=payload.id_estado,
        detalle_consulta=payload.detalle_consulta.strip(),
        detalle_diagnostico=payload.detalle_diagnostico.strip() if payload.detalle_diagnostico else None,
        fecha_ingreso=datetime.now(),
    )
    db.add(nueva)
    db.flush()

    # Crear registro de facturación vinculado automáticamente a la consulta
    factura = Facturacion(id_consulta=nueva.id_consulta)
    db.add(factura)
    db.commit()
    db.refresh(nueva)

    return _build_consulta_response(nueva)


@app.put("/api/consultas/{id_consulta}", response_model=ConsultaResponse)
def actualizar_consulta(
    id_consulta: int,
    payload: ConsultaUpdate,
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista", "Mecanico")),
    db: Session = Depends(get_db),
):
    consulta = db.query(Consulta).filter(Consulta.id_consulta == id_consulta).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada.")

    if payload.id_usuario is not None:
        mecanico = db.query(Usuario).filter(Usuario.id_usuario == payload.id_usuario).first()
        if not mecanico or not mecanico.rol or mecanico.rol.nombre.lower() not in ("mecanico", "mecánico"):
            raise HTTPException(
                status_code=400,
                detail="Solo se puede asignar un usuario con rol Mecánico.",
            )
        consulta.id_usuario = payload.id_usuario

    if payload.detalle_consulta is not None:
        consulta.detalle_consulta = payload.detalle_consulta.strip()

    if payload.detalle_diagnostico is not None:
        consulta.detalle_diagnostico = payload.detalle_diagnostico.strip()

    if payload.finalizar:
        if IS_POSTGRES:
            db.execute(
                text("SELECT sp_finalizar_consulta(:id_c, :diag)"),
                {"id_c": id_consulta, "diag": consulta.detalle_diagnostico},
            )
        else:
            estado_fin = db.query(Estado).filter(func.lower(Estado.nombre) == "finalizado").first()
            if estado_fin:
                consulta.id_estado = estado_fin.id_estado
            consulta.fecha_salida = datetime.now()
            if not consulta.factura:
                db.add(Facturacion(id_consulta=consulta.id_consulta))
    elif payload.id_estado is not None:
        consulta.id_estado = payload.id_estado
        estado_obj = db.query(Estado).filter(Estado.id_estado == payload.id_estado).first()
        if estado_obj and estado_obj.nombre.lower() == "finalizado" and not consulta.fecha_salida:
            consulta.fecha_salida = datetime.now()

    db.commit()
    db.refresh(consulta)
    return _build_consulta_response(consulta)


# =============================================================================
# 7. MÓDULO DE PRODUCTOS, BUSCADOR API SPEERO E INVENTARIO (Bodeguero, Mecánico, Admin)
# =============================================================================
@app.get("/api/productos/buscar-externo")
def buscar_productos_speero(
    q: str = Query(..., min_length=1, description="Término de búsqueda de repuesto"),
    current_user: Usuario = Depends(require_roles("Administrador", "Bodeguero")),
):
    """
    Intenta consultar el catálogo externo en https://speero.net/api/v1.
    Si la API externa no responde, requiere autenticación o devuelve error,
    informa claramente al frontend para habilitar el ingreso manual con URL/Base64.
    """
    headers = {"Accept": "application/json"}
    if SPEERO_API_KEY:
        headers["Authorization"] = f"Bearer {SPEERO_API_KEY}"

    candidate_urls = [
        f"{SPEERO_API_URL}/products",
        f"{SPEERO_API_URL}/parts",
        f"{SPEERO_API_URL}/search",
        SPEERO_API_URL,
    ]

    for url in candidate_urls:
        try:
            resp = requests.get(
                url,
                params={"q": q, "search": q, "query": q},
                headers=headers,
                timeout=4,
            )
            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    data = resp.json()
                    raw_items = (
                        data
                        if isinstance(data, list)
                        else data.get("data") or data.get("products") or data.get("items") or data.get("results") or []
                    )
                    if isinstance(raw_items, list) and len(raw_items) > 0:
                        normalized = []
                        for idx, item in enumerate(raw_items[:20]):
                            if isinstance(item, dict):
                                nombre = (
                                    item.get("name")
                                    or item.get("nombre")
                                    or item.get("title")
                                    or item.get("description")
                                    or f"Repuesto Speero #{idx + 1}"
                                )
                                imagen = (
                                    item.get("image")
                                    or item.get("url_imagen")
                                    or item.get("image_url")
                                    or item.get("thumbnail")
                                    or ""
                                )
                                precio = float(item.get("price") or item.get("cost") or item.get("costo") or 120.0)
                                normalized.append(
                                    {
                                        "sku": str(item.get("id") or item.get("sku") or f"SP-{idx+100}"),
                                        "nombre": nombre,
                                        "url_imagen": imagen,
                                        "precio_sugerido": precio,
                                        "origen": "Speero API v1",
                                    }
                                )
                        return {
                            "api_online": True,
                            "endpoint_consultado": url,
                            "query": q,
                            "resultados": normalized,
                            "mensaje": f"Se encontraron {len(normalized)} resultados en {SPEERO_API_URL}.",
                        }
        except Exception:
            continue

    return {
        "api_online": False,
        "endpoint_consultado": SPEERO_API_URL,
        "query": q,
        "resultados": [],
        "mensaje": (
            f"El servicio externo ({SPEERO_API_URL}) no devolvió resultados o no se encuentra disponible en este momento. "
            "Puedes registrar la compra manualmente ingresando los datos del repuesto y su imagen (URL o Base64)."
        ),
    }


@app.get("/api/productos", response_model=List[ProductoCatalogoResponse])
def listar_productos(
    q: Optional[str] = Query(default=None),
    current_user: Usuario = Depends(require_roles("Administrador", "Bodeguero", "Mecanico")),
    db: Session = Depends(get_db),
):
    query = db.query(Producto)
    if q:
        query = query.filter(Producto.nombre.ilike(f"%{q.strip()}%"))

    productos = query.order_by(Producto.id_producto.desc()).all()
    resultado = []
    for p in productos:
        stock_total, ultimo_costo_compra, precio_venta_actual = _get_producto_stats(db, p.id_producto)
        resultado.append(
            ProductoCatalogoResponse(
                id_producto=p.id_producto,
                nombre=p.nombre,
                url_imagen=p.url_imagen,
                stock_total=stock_total,
                ultimo_costo_compra=ultimo_costo_compra,
                precio_venta_actual=precio_venta_actual,
            )
        )
    return resultado


@app.get("/api/inventario", response_model=List[InventarioLoteResponse])
def listar_inventario(
    current_user: Usuario = Depends(require_roles("Administrador", "Bodeguero")),
    db: Session = Depends(get_db),
):
    lotes = (
        db.query(Inventario)
        .join(Producto, Inventario.id_producto == Producto.id_producto)
        .order_by(Inventario.fecha_compra.desc(), Inventario.id_inventario.desc())
        .all()
    )
    return [
        InventarioLoteResponse(
            id_inventario=l.id_inventario,
            id_producto=l.id_producto,
            producto_nombre=l.producto.nombre if l.producto else "",
            url_imagen=l.producto.url_imagen if l.producto else None,
            costo_compra=float(l.costo_compra),
            costo_venta=float(l.costo_venta),
            fecha_compra=l.fecha_compra,
            cantidad=l.cantidad,
        )
        for l in lotes
    ]


@app.post("/api/inventario/comprar", response_model=InventarioLoteResponse, status_code=status.HTTP_201_CREATED)
def comprar_producto_bodega(
    payload: ProductoCompraCreate,
    current_user: Usuario = Depends(require_roles("Administrador", "Bodeguero")),
    db: Session = Depends(get_db),
):
    """
    Registra la compra de un repuesto por parte del Bodeguero:
    1. Si el producto no existe en `productos`, lo crea con su `nombre` y `url_imagen` (URL o Base64).
    2. Registra el ingreso en `inventario` con `costo_compra`, `costo_venta = costo_compra * 1.2` y `cantidad`.
    """
    nombre_clean = payload.nombre.strip()
    img_clean = payload.url_imagen.strip() if payload.url_imagen else None

    if IS_POSTGRES:
        row = db.execute(
            text(
                "SELECT * FROM sp_comprar_producto_bodega(:nom, :img, :costo, :cant, :id_prod)"
            ),
            {
                "nom": nombre_clean,
                "img": img_clean,
                "costo": Decimal(str(round(payload.costo_compra, 2))),
                "cant": payload.cantidad,
                "id_prod": payload.id_producto,
            },
        ).fetchone()
        db.commit()
        lote = db.query(Inventario).filter(Inventario.id_inventario == row.out_id_inventario).first()
    else:
        producto = None
        if payload.id_producto:
            producto = db.query(Producto).filter(Producto.id_producto == payload.id_producto).first()
        if not producto:
            producto = (
                db.query(Producto)
                .filter(func.lower(Producto.nombre) == nombre_clean.lower())
                .first()
            )
        if not producto:
            producto = Producto(nombre=nombre_clean, url_imagen=img_clean)
            db.add(producto)
            db.flush()
        elif img_clean:
            producto.url_imagen = img_clean

        costo_c = Decimal(str(round(payload.costo_compra, 2)))
        costo_v = Decimal(str(round(payload.costo_compra * 1.20, 2)))

        lote = Inventario(
            id_producto=producto.id_producto,
            costo_compra=costo_c,
            costo_venta=costo_v,
            fecha_compra=datetime.now(),
            cantidad=payload.cantidad,
        )
        db.add(lote)
        db.commit()
        db.refresh(lote)

    return InventarioLoteResponse(
        id_inventario=lote.id_inventario,
        id_producto=lote.id_producto,
        producto_nombre=lote.producto.nombre if lote.producto else nombre_clean,
        url_imagen=lote.producto.url_imagen if lote.producto else img_clean,
        costo_compra=float(lote.costo_compra),
        costo_venta=float(lote.costo_venta),
        fecha_compra=lote.fecha_compra,
        cantidad=lote.cantidad,
    )


# =============================================================================
# 8. SOLICITUDES DE REPUESTOS Y DESPACHO AUTOMÁTICO A KARDEX/FACTURA
# =============================================================================
@app.get("/api/solicitudes", response_model=List[SolicitudRepuestoResponse])
def listar_solicitudes(
    estado: Optional[str] = Query(default=None),
    id_consulta: Optional[int] = Query(default=None),
    current_user: Usuario = Depends(require_roles("Administrador", "Mecanico", "Bodeguero")),
    db: Session = Depends(get_db),
):
    query = db.query(SolicitudRepuesto)
    if id_consulta is not None:
        query = query.filter(SolicitudRepuesto.id_consulta == id_consulta)
    if estado:
        query = query.join(Estado, SolicitudRepuesto.id_estado == Estado.id_estado).filter(
            func.lower(Estado.nombre) == estado.strip().lower()
        )

    solicitudes = query.order_by(SolicitudRepuesto.fecha_solicitud.desc(), SolicitudRepuesto.id_solicitud.desc()).all()
    resultado = []
    for s in solicitudes:
        stock_disp, _, precio_venta = _get_producto_stats(db, s.id_producto)
        placa = s.consulta.vehiculo.placa if (s.consulta and s.consulta.vehiculo) else f"Consulta #{s.id_consulta}"
        resultado.append(
            SolicitudRepuestoResponse(
                id_solicitud=s.id_solicitud,
                id_consulta=s.id_consulta,
                vehiculo_placa=placa,
                id_producto=s.id_producto,
                producto_nombre=s.producto.nombre if s.producto else "",
                url_imagen=s.producto.url_imagen if s.producto else None,
                id_usuario_solicitante=s.id_usuario_solicitante,
                solicitante_nombre=(
                    s.solicitante.persona.nombre
                    if (s.solicitante and s.solicitante.persona)
                    else (s.solicitante.alias if s.solicitante else "Mecánico")
                ),
                id_usuario_despachador=s.id_usuario_despachador,
                despachador_nombre=(
                    s.despachador.persona.nombre
                    if (s.despachador and s.despachador.persona)
                    else (s.despachador.alias if s.despachador else None)
                ),
                id_estado=s.id_estado,
                estado_nombre=s.estado.nombre if s.estado else "Pendiente",
                cantidad=s.cantidad,
                stock_disponible=stock_disp,
                precio_venta_unitario=precio_venta,
                sub_total_estimado=round(precio_venta * s.cantidad, 2),
                fecha_solicitud=s.fecha_solicitud,
                fecha_despacho=s.fecha_despacho,
            )
        )
    return resultado


@app.post("/api/solicitudes", response_model=SolicitudRepuestoResponse, status_code=status.HTTP_201_CREATED)
def crear_solicitud_repuesto(
    payload: SolicitudRepuestoCreate,
    current_user: Usuario = Depends(require_roles("Administrador", "Mecanico")),
    db: Session = Depends(get_db),
):
    consulta = db.query(Consulta).filter(Consulta.id_consulta == payload.id_consulta).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="La consulta indicada no existe.")

    producto = db.query(Producto).filter(Producto.id_producto == payload.id_producto).first()
    if not producto:
        raise HTTPException(status_code=404, detail="El producto solicitado no existe.")

    stock_disp, _, precio_venta = _get_producto_stats(db, payload.id_producto)
    if stock_disp < payload.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente en bodega. Disponible: {stock_disp}, Solicitado: {payload.cantidad}.",
        )

    if IS_POSTGRES:
        row = db.execute(
            text("SELECT sp_solicitar_repuesto(:id_c, :id_p, :id_u, :cant) AS id_sol"),
            {
                "id_c": payload.id_consulta,
                "id_p": payload.id_producto,
                "id_u": current_user.id_usuario,
                "cant": payload.cantidad,
            },
        ).fetchone()
        db.commit()
        nueva = db.query(SolicitudRepuesto).filter(SolicitudRepuesto.id_solicitud == row.id_sol).first()
    else:
        estado_pend = db.query(Estado).filter(func.lower(Estado.nombre) == "pendiente").first()
        nueva = SolicitudRepuesto(
            id_consulta=payload.id_consulta,
            id_producto=payload.id_producto,
            id_usuario_solicitante=current_user.id_usuario,
            id_estado=estado_pend.id_estado if estado_pend else 3,
            cantidad=payload.cantidad,
            fecha_solicitud=datetime.now(),
        )
        db.add(nueva)
        db.commit()
        db.refresh(nueva)

    placa = nueva.consulta.vehiculo.placa if (nueva.consulta and nueva.consulta.vehiculo) else ""
    return SolicitudRepuestoResponse(
        id_solicitud=nueva.id_solicitud,
        id_consulta=nueva.id_consulta,
        vehiculo_placa=placa,
        id_producto=nueva.id_producto,
        producto_nombre=producto.nombre,
        url_imagen=producto.url_imagen,
        id_usuario_solicitante=nueva.id_usuario_solicitante,
        solicitante_nombre=current_user.persona.nombre if current_user.persona else current_user.alias,
        id_usuario_despachador=None,
        despachador_nombre=None,
        id_estado=nueva.id_estado,
        estado_nombre=nueva.estado.nombre if nueva.estado else "Pendiente",
        cantidad=nueva.cantidad,
        stock_disponible=stock_disp,
        precio_venta_unitario=precio_venta,
        sub_total_estimado=round(precio_venta * nueva.cantidad, 2),
        fecha_solicitud=nueva.fecha_solicitud,
        fecha_despacho=None,
    )


@app.post("/api/solicitudes/{id_solicitud}/despachar")
def despachar_solicitud_repuesto(
    id_solicitud: int,
    current_user: Usuario = Depends(require_roles("Administrador", "Bodeguero")),
    db: Session = Depends(get_db),
):
    """
    El Bodeguero despacha la solicitud del Mecánico:
    1. Verifica y descuenta del inventario (FIFO).
    2. Garantiza la existencia de la factura para la consulta (`facturacion`).
    3. Inserta automáticamente el movimiento en `kardex` con `sub_total = cantidad * costo_venta`.
    4. Marca la solicitud como `Despachado`.
    """
    solicitud = db.query(SolicitudRepuesto).filter(SolicitudRepuesto.id_solicitud == id_solicitud).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud de repuesto no encontrada.")

    if solicitud.estado and solicitud.estado.nombre.lower() != "pendiente":
        raise HTTPException(status_code=400, detail=f"La solicitud ya fue procesada ({solicitud.estado.nombre}).")

    if IS_POSTGRES:
        try:
            row = db.execute(
                text("SELECT * FROM sp_despachar_repuesto(:id_sol, :id_bod)"),
                {"id_sol": id_solicitud, "id_bod": current_user.id_usuario},
            ).fetchone()
            db.commit()
            return {
                "mensaje": "Repuesto despachado e integrado automáticamente al Kardex y Factura.",
                "id_solicitud": row.out_id_solicitud,
                "id_factura": row.out_id_factura,
                "id_kardex": row.out_id_kardex,
                "sub_total": float(row.out_sub_total),
            }
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(exc))
    else:
        lotes = (
            db.query(Inventario)
            .filter(Inventario.id_producto == solicitud.id_producto, Inventario.cantidad > 0)
            .order_by(Inventario.fecha_compra.asc(), Inventario.id_inventario.asc())
            .all()
        )
        stock_total = sum(l.cantidad for l in lotes)
        if stock_total < solicitud.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente en inventario para despachar. Disponible: {stock_total}, Requerido: {solicitud.cantidad}.",
            )

        restante = solicitud.cantidad
        sub_total_acum = Decimal("0.00")
        for lote in lotes:
            if restante <= 0:
                break
            tomar = min(lote.cantidad, restante)
            lote.cantidad -= tomar
            sub_total_acum += Decimal(str(tomar)) * Decimal(str(lote.costo_venta))
            restante -= tomar

        factura = db.query(Facturacion).filter(Facturacion.id_consulta == solicitud.id_consulta).first()
        if not factura:
            factura = Facturacion(id_consulta=solicitud.id_consulta)
            db.add(factura)
            db.flush()

        mov_kardex = Kardex(
            id_factura=factura.id_factura,
            id_producto=solicitud.id_producto,
            cantidad=solicitud.cantidad,
            sub_total=round(sub_total_acum, 2),
        )
        db.add(mov_kardex)
        db.flush()

        estado_desp = db.query(Estado).filter(func.lower(Estado.nombre) == "despachado").first()
        solicitud.id_estado = estado_desp.id_estado if estado_desp else 7
        solicitud.id_usuario_despachador = current_user.id_usuario
        solicitud.fecha_despacho = datetime.now()

        db.commit()
        return {
            "mensaje": "Repuesto despachado e integrado automáticamente al Kardex y Factura.",
            "id_solicitud": solicitud.id_solicitud,
            "id_factura": factura.id_factura,
            "id_kardex": mov_kardex.id_kardex,
            "sub_total": float(mov_kardex.sub_total),
        }


@app.post("/api/solicitudes/{id_solicitud}/rechazar")
def rechazar_solicitud_repuesto(
    id_solicitud: int,
    current_user: Usuario = Depends(require_roles("Administrador", "Bodeguero")),
    db: Session = Depends(get_db),
):
    solicitud = db.query(SolicitudRepuesto).filter(SolicitudRepuesto.id_solicitud == id_solicitud).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")

    if solicitud.estado and solicitud.estado.nombre.lower() != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden rechazar solicitudes en estado Pendiente.")

    estado_rech = db.query(Estado).filter(func.lower(Estado.nombre) == "rechazado").first()
    solicitud.id_estado = estado_rech.id_estado if estado_rech else 8
    solicitud.id_usuario_despachador = current_user.id_usuario
    solicitud.fecha_despacho = datetime.now()
    db.commit()
    return {"mensaje": f"Solicitud #{id_solicitud} marcada como Rechazada."}


# =============================================================================
# 9. MÓDULO DE FACTURACIÓN Y KARDEX (Administrador, Recepcionista, Bodeguero)
# =============================================================================
def _build_factura_detalle(f: Facturacion) -> FacturaDetalleResponse:
    c = f.consulta
    v = c.vehiculo if c else None
    p = v.propietario if v else None
    m = c.mecanico if c else None

    items = []
    total_f = 0.0
    total_unidades = 0
    for k in f.items_kardex:
        sub = float(k.sub_total)
        unit = round(sub / k.cantidad, 2) if k.cantidad > 0 else 0.0
        total_f += sub
        total_unidades += k.cantidad
        items.append(
            KardexItemResponse(
                id_kardex=k.id_kardex,
                id_factura=k.id_factura,
                id_producto=k.id_producto,
                producto_nombre=k.producto.nombre if k.producto else f"Producto #{k.id_producto}",
                url_imagen=k.producto.url_imagen if k.producto else None,
                cantidad=k.cantidad,
                precio_unitario=unit,
                sub_total=sub,
            )
        )

    return FacturaDetalleResponse(
        id_factura=f.id_factura,
        id_consulta=f.id_consulta,
        fecha_ingreso=c.fecha_ingreso if c else datetime.now(),
        fecha_salida=c.fecha_salida if c else None,
        estado_consulta=c.estado.nombre if (c and c.estado) else "Activa",
        cliente_nombre=p.nombre if p else "Sin cliente",
        cliente_nit=p.nit if p else "C/F",
        cliente_telefono=p.telefono if p else None,
        cliente_email=p.email if p else None,
        vehiculo_placa=v.placa if v else "N/A",
        vehiculo_vin=v.vin if v else "N/A",
        mecanico_nombre=m.persona.nombre if (m and m.persona) else (m.alias if m else "N/A"),
        detalle_consulta=c.detalle_consulta if c else "",
        detalle_diagnostico=c.detalle_diagnostico if c else None,
        items_kardex=items,
        total_items=total_unidades,
        total_factura=round(total_f, 2),
    )


@app.get("/api/facturacion", response_model=List[FacturaDetalleResponse])
def listar_facturas(
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista", "Bodeguero")),
    db: Session = Depends(get_db),
):
    # Asegurar que toda consulta tenga su registro en facturacion para visibilidad completa
    consultas_sin_factura = (
        db.query(Consulta)
        .outerjoin(Facturacion, Consulta.id_consulta == Facturacion.id_consulta)
        .filter(Facturacion.id_factura.is_(None))
        .all()
    )
    if consultas_sin_factura:
        for c in consultas_sin_factura:
            db.add(Facturacion(id_consulta=c.id_consulta))
        db.commit()

    facturas = db.query(Facturacion).order_by(Facturacion.id_factura.desc()).all()
    return [_build_factura_detalle(f) for f in facturas]


@app.get("/api/facturacion/{id_factura}", response_model=FacturaDetalleResponse)
def obtener_factura(
    id_factura: int,
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista", "Bodeguero")),
    db: Session = Depends(get_db),
):
    f = db.query(Facturacion).filter(Facturacion.id_factura == id_factura).first()
    if not f:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")
    return _build_factura_detalle(f)


@app.get("/api/kardex", response_model=List[KardexItemResponse])
def listar_kardex(
    id_factura: Optional[int] = Query(default=None),
    current_user: Usuario = Depends(require_roles("Administrador", "Recepcionista", "Bodeguero")),
    db: Session = Depends(get_db),
):
    query = db.query(Kardex)
    if id_factura is not None:
        query = query.filter(Kardex.id_factura == id_factura)

    movimientos = query.order_by(Kardex.id_kardex.desc()).all()
    return [
        KardexItemResponse(
            id_kardex=k.id_kardex,
            id_factura=k.id_factura,
            id_producto=k.id_producto,
            producto_nombre=k.producto.nombre if k.producto else "",
            url_imagen=k.producto.url_imagen if k.producto else None,
            cantidad=k.cantidad,
            precio_unitario=round(float(k.sub_total) / k.cantidad, 2) if k.cantidad > 0 else 0.0,
            sub_total=float(k.sub_total),
        )
        for k in movimientos
    ]


# =============================================================================
# 10. ARCHIVOS ESTÁTICOS DEL FRONTEND (FASE 3)
# =============================================================================
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_frontend():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Taller Pro API funcionando. Frontend pendiente de compilación."}
