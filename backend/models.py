from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from backend.database import Base


class Persona(Base):
    __tablename__ = "personas"

    id_persona = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    telefono = Column(String(30), nullable=True)
    email = Column(String(120), unique=True, nullable=True)
    edad = Column(Integer, nullable=True)
    sexo = Column(String(20), nullable=True)
    nit = Column(String(30), unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="persona")
    vehiculos = relationship("Vehiculo", back_populates="propietario")


class Rol(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion_corta = Column(String(255), nullable=True)

    usuarios = relationship("Usuario", back_populates="rol")


class Estado(Base):
    __tablename__ = "estados"

    id_estado = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(50), unique=True, nullable=False)


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    id_persona = Column(Integer, ForeignKey("personas.id_persona"), nullable=False)
    id_estado = Column(Integer, ForeignKey("estados.id_estado"), nullable=False)
    alias = Column(String(60), unique=True, nullable=False, index=True)
    contrasenia = Column(Text, nullable=False)
    token = Column(Text, nullable=True)

    rol = relationship("Rol", back_populates="usuarios")
    persona = relationship("Persona", back_populates="usuarios")
    estado = relationship("Estado")
    consultas_asignadas = relationship("Consulta", back_populates="mecanico")


class Vehiculo(Base):
    __tablename__ = "vehiculo"

    id_vehiculo = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_persona = Column(Integer, ForeignKey("personas.id_persona"), nullable=False)
    vin = Column(String(50), unique=True, nullable=False)
    placa = Column(String(20), unique=True, nullable=False)

    propietario = relationship("Persona", back_populates="vehiculos")
    consultas = relationship("Consulta", back_populates="vehiculo")


class Consulta(Base):
    __tablename__ = "consultas"

    id_consulta = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_vehiculo = Column(Integer, ForeignKey("vehiculo.id_vehiculo"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_estado = Column(Integer, ForeignKey("estados.id_estado"), nullable=False)
    detalle_consulta = Column(Text, nullable=False)
    detalle_diagnostico = Column(Text, nullable=True)
    fecha_ingreso = Column(DateTime, nullable=False, default=datetime.now)
    fecha_salida = Column(DateTime, nullable=True)

    vehiculo = relationship("Vehiculo", back_populates="consultas")
    mecanico = relationship("Usuario", back_populates="consultas_asignadas")
    estado = relationship("Estado")
    factura = relationship("Facturacion", back_populates="consulta", uselist=False)
    solicitudes = relationship("SolicitudRepuesto", back_populates="consulta")


class Producto(Base):
    __tablename__ = "productos"

    id_producto = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    url_imagen = Column(Text, nullable=True)

    lotes_inventario = relationship("Inventario", back_populates="producto")
    movimientos_kardex = relationship("Kardex", back_populates="producto")


class Inventario(Base):
    __tablename__ = "inventario"

    id_inventario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    costo_compra = Column(Numeric(12, 2), nullable=False)
    costo_venta = Column(Numeric(12, 2), nullable=False)
    fecha_compra = Column(DateTime, nullable=False, default=datetime.now)
    cantidad = Column(Integer, nullable=False, default=0)

    producto = relationship("Producto", back_populates="lotes_inventario")


class Facturacion(Base):
    __tablename__ = "facturacion"

    id_factura = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_consulta = Column(Integer, ForeignKey("consultas.id_consulta"), unique=True, nullable=False)

    consulta = relationship("Consulta", back_populates="factura")
    items_kardex = relationship("Kardex", back_populates="factura")


class Kardex(Base):
    __tablename__ = "kardex"

    id_kardex = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_factura = Column(Integer, ForeignKey("facturacion.id_factura"), nullable=False)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    sub_total = Column(Numeric(12, 2), nullable=False)

    factura = relationship("Facturacion", back_populates="items_kardex")
    producto = relationship("Producto", back_populates="movimientos_kardex")


class SolicitudRepuesto(Base):
    __tablename__ = "solicitudes_repuestos"

    id_solicitud = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_consulta = Column(Integer, ForeignKey("consultas.id_consulta"), nullable=False)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    id_usuario_solicitante = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_usuario_despachador = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    id_estado = Column(Integer, ForeignKey("estados.id_estado"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    fecha_solicitud = Column(DateTime, nullable=False, default=datetime.now)
    fecha_despacho = Column(DateTime, nullable=True)

    consulta = relationship("Consulta", back_populates="solicitudes")
    producto = relationship("Producto")
    solicitante = relationship("Usuario", foreign_keys=[id_usuario_solicitante])
    despachador = relationship("Usuario", foreign_keys=[id_usuario_despachador])
    estado = relationship("Estado")
