from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# =============================================================================
# AUTENTICACIÓN
# =============================================================================
class LoginRequest(BaseModel):
    alias: str
    contrasenia: str


class TokenUserResponse(BaseModel):
    id_usuario: int
    alias: str
    id_rol: int
    rol_nombre: str
    id_persona: int
    persona_nombre: str
    id_estado: int
    estado_nombre: str
    token: str


# =============================================================================
# ROLES Y ESTADOS
# =============================================================================
class RolBase(BaseModel):
    nombre: str
    descripcion_corta: Optional[str] = None


class RolResponse(RolBase):
    id_rol: int

    class Config:
        from_attributes = True


class EstadoBase(BaseModel):
    nombre: str


class EstadoResponse(EstadoBase):
    id_estado: int

    class Config:
        from_attributes = True


# =============================================================================
# PERSONAS
# =============================================================================
class PersonaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150)
    telefono: Optional[str] = None
    email: Optional[str] = None
    edad: Optional[int] = Field(default=None, ge=0, le=130)
    sexo: Optional[str] = None
    nit: str = Field(..., min_length=2, max_length=30)


class PersonaUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    edad: Optional[int] = None
    sexo: Optional[str] = None
    nit: Optional[str] = None


class PersonaResponse(PersonaCreate):
    id_persona: int

    class Config:
        from_attributes = True


# =============================================================================
# USUARIOS
# =============================================================================
class UsuarioCreate(BaseModel):
    id_rol: int
    id_persona: int
    id_estado: int = 1
    alias: str = Field(..., min_length=3, max_length=60)
    contrasenia: str = Field(..., min_length=4)


class UsuarioUpdate(BaseModel):
    id_rol: Optional[int] = None
    id_persona: Optional[int] = None
    id_estado: Optional[int] = None
    alias: Optional[str] = None
    contrasenia: Optional[str] = None


class UsuarioResponse(BaseModel):
    id_usuario: int
    id_rol: int
    rol_nombre: str
    id_persona: int
    persona_nombre: str
    id_estado: int
    estado_nombre: str
    alias: str

    class Config:
        from_attributes = True


# =============================================================================
# VEHÍCULOS
# =============================================================================
class VehiculoCreate(BaseModel):
    id_persona: int
    vin: str = Field(..., min_length=3, max_length=50)
    placa: str = Field(..., min_length=2, max_length=20)


class VehiculoUpdate(BaseModel):
    id_persona: Optional[int] = None
    vin: Optional[str] = None
    placa: Optional[str] = None


class VehiculoResponse(BaseModel):
    id_vehiculo: int
    id_persona: int
    propietario_nombre: str
    propietario_nit: str
    vin: str
    placa: str

    class Config:
        from_attributes = True


# =============================================================================
# CONSULTAS
# =============================================================================
class ConsultaCreate(BaseModel):
    id_vehiculo: int
    id_usuario: int
    id_estado: int = 3
    detalle_consulta: str
    detalle_diagnostico: Optional[str] = None


class ConsultaUpdate(BaseModel):
    id_usuario: Optional[int] = None
    id_estado: Optional[int] = None
    detalle_consulta: Optional[str] = None
    detalle_diagnostico: Optional[str] = None
    finalizar: Optional[bool] = False


class ConsultaResponse(BaseModel):
    id_consulta: int
    id_vehiculo: int
    vehiculo_placa: str
    vehiculo_vin: str
    propietario_nombre: str
    id_usuario: int
    mecanico_nombre: str
    mecanico_alias: str
    id_estado: int
    estado_nombre: str
    detalle_consulta: str
    detalle_diagnostico: Optional[str] = None
    fecha_ingreso: datetime
    fecha_salida: Optional[datetime] = None
    id_factura: Optional[int] = None


# =============================================================================
# PRODUCTOS E INVENTARIO (BODEGA)
# =============================================================================
class ProductoCompraCreate(BaseModel):
    id_producto: Optional[int] = None
    nombre: str = Field(..., min_length=2, max_length=200)
    url_imagen: Optional[str] = None
    costo_compra: float = Field(..., gt=0)
    cantidad: int = Field(..., gt=0)


class ProductoCatalogoResponse(BaseModel):
    id_producto: int
    nombre: str
    url_imagen: Optional[str] = None
    stock_total: int
    ultimo_costo_compra: float
    precio_venta_actual: float


class InventarioLoteResponse(BaseModel):
    id_inventario: int
    id_producto: int
    producto_nombre: str
    url_imagen: Optional[str] = None
    costo_compra: float
    costo_venta: float
    fecha_compra: datetime
    cantidad: int


# =============================================================================
# SOLICITUDES DE REPUESTOS (MECÁNICO -> BODEGUERO)
# =============================================================================
class SolicitudRepuestoCreate(BaseModel):
    id_consulta: int
    id_producto: int
    cantidad: int = Field(..., gt=0)


class SolicitudRepuestoResponse(BaseModel):
    id_solicitud: int
    id_consulta: int
    vehiculo_placa: str
    id_producto: int
    producto_nombre: str
    url_imagen: Optional[str] = None
    id_usuario_solicitante: int
    solicitante_nombre: str
    id_usuario_despachador: Optional[int] = None
    despachador_nombre: Optional[str] = None
    id_estado: int
    estado_nombre: str
    cantidad: int
    stock_disponible: int
    precio_venta_unitario: float
    sub_total_estimado: float
    fecha_solicitud: datetime
    fecha_despacho: Optional[datetime] = None


# =============================================================================
# FACTURACIÓN Y KARDEX
# =============================================================================
class KardexItemResponse(BaseModel):
    id_kardex: int
    id_factura: int
    id_producto: int
    producto_nombre: str
    url_imagen: Optional[str] = None
    cantidad: int
    precio_unitario: float
    sub_total: float


class FacturaDetalleResponse(BaseModel):
    id_factura: int
    id_consulta: int
    fecha_ingreso: datetime
    fecha_salida: Optional[datetime] = None
    estado_consulta: str
    cliente_nombre: str
    cliente_nit: str
    cliente_telefono: Optional[str] = None
    cliente_email: Optional[str] = None
    vehiculo_placa: str
    vehiculo_vin: str
    mecanico_nombre: str
    detalle_consulta: str
    detalle_diagnostico: Optional[str] = None
    items_kardex: List[KardexItemResponse]
    total_items: int
    total_factura: float
