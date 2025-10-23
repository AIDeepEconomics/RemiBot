from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.catalog_service import CatalogService
from app.core.log_service import LogService
from app.core.qrcode_service import QRCodeService
from app.core.remito_service import RemitoService
from app.models.remito import Remito, RemitoCreate


class CreateRemitoUseCase:
    """Caso de uso para crear un remito con todas sus dependencias."""

    def __init__(
        self,
        remito_service: RemitoService,
        catalog_service: CatalogService,
        qrcode_service: QRCodeService,
        log_service: LogService,
    ) -> None:
        self.remito_service = remito_service
        self.catalog_service = catalog_service
        self.qrcode_service = qrcode_service
        self.log_service = log_service

    async def execute(
        self,
        remito_data: Dict[str, Any],
        contact: str,
    ) -> Remito:
        """
        Ejecuta la creación de un remito completo.
        
        Args:
            remito_data: Datos del remito desde el LLM
            contact: Número de teléfono del usuario
            
        Returns:
            El remito creado con QR y todos los datos
        """
        try:
            # 1. Crear o obtener entidades del catálogo
            empresa = await self._get_or_create_empresa(remito_data["nombre_empresa"])
            establecimiento = await self._get_or_create_establecimiento(
                remito_data["nombre_establecimiento"], 
                empresa["id_empresa"]
            )
            chacra = await self._get_or_create_chacra(
                remito_data["nombre_chacra"],
                establecimiento["id_establecimiento"],
                empresa["id_empresa"],
            )
            destino = await self._get_or_create_destino(remito_data["nombre_destino"])

            # 2. Crear payload del remito
            remito_payload = RemitoCreate(
                id_chacra=chacra["id_chacra"],
                nombre_chacra=remito_data["nombre_chacra"],
                id_establecimiento=establecimiento["id_establecimiento"],
                nombre_establecimiento=remito_data["nombre_establecimiento"],
                id_empresa=empresa["id_empresa"],
                nombre_empresa=remito_data["nombre_empresa"],
                id_destino=destino["id_destino"],
                nombre_destino=remito_data["nombre_destino"],
                nombre_conductor=remito_data["nombre_conductor"],
                cedula_conductor=remito_data["cedula_conductor"],
                matricula_camion=remito_data["matricula_camion"],
                matricula_zorra=remito_data.get("matricula_zorra"),
                peso_estimado_tn=float(remito_data["peso_estimado_tn"]),
                raw_payload={**remito_data, "contacto": contact},
            )

            # 3. Crear remito en Supabase (incluye generación de QR)
            remito = await self.remito_service.create_remito(remito_payload)

            # 4. Registrar log de creación exitosa
            await self.log_service.write_log(
                tipo="REMITO",
                detalle=f"Remito {remito.id_remito} creado exitosamente",
                payload={
                    "id_remito": remito.id_remito,
                    "contacto": contact,
                    "empresa": remito.nombre_empresa,
                    "establecimiento": remito.nombre_establecimiento,
                    "chacra": remito.nombre_chacra,
                    "conductor": remito.nombre_conductor,
                },
            )

            return remito

        except Exception as e:
            # Registrar error y propagar
            await self.log_service.write_log(
                tipo="ERROR",
                detalle=f"Error creando remito: {str(e)}",
                payload={"contacto": contact, "data": remito_data, "error": str(e)},
            )
            raise

    async def _get_or_create_empresa(self, nombre: str) -> Dict[str, Any]:
        """Obtiene o crea una empresa."""
        empresa = await self.catalog_service.get_or_create_empresa(nombre)
        await self.log_service.write_log(
            tipo="DEBUG",
            detalle=f"Empresa procesada: {nombre} -> {empresa['id_empresa']}",
            payload={"empresa_id": empresa["id_empresa"], "nombre": nombre},
        )
        return empresa

    async def _get_or_create_establecimiento(
        self, 
        nombre: str, 
        empresa_id: str
    ) -> Dict[str, Any]:
        """Obtiene o crea un establecimiento."""
        establecimiento = await self.catalog_service.get_or_create_establecimiento(
            nombre, empresa_id
        )
        await self.log_service.write_log(
            tipo="DEBUG",
            detalle=f"Establecimiento procesado: {nombre} -> {establecimiento['id_establecimiento']}",
            payload={
                "establecimiento_id": establecimiento["id_establecimiento"],
                "nombre": nombre,
                "empresa_id": empresa_id,
            },
        )
        return establecimiento

    async def _get_or_create_chacra(
        self,
        nombre_chacra: str,
        establecimiento_id: str,
        empresa_id: str,
    ) -> Dict[str, Any]:
        """Obtiene o crea una chacra."""
        chacra = await self.catalog_service.get_or_create_chacra(
            nombre_chacra, establecimiento_id, empresa_id
        )
        await self.log_service.write_log(
            tipo="DEBUG",
            detalle=f"Chacra procesada: {nombre_chacra} -> {chacra['id_chacra']}",
            payload={
                "chacra_id": chacra["id_chacra"],
                "nombre": nombre_chacra,
                "establecimiento_id": establecimiento_id,
            },
        )
        return chacra

    async def _get_or_create_destino(self, nombre: str) -> Dict[str, Any]:
        """Obtiene o crea un destino."""
        destino = await self.catalog_service.get_or_create_destino(nombre)
        await self.log_service.write_log(
            tipo="DEBUG",
            detalle=f"Destino procesado: {nombre} -> {destino['id_destino']}",
            payload={"destino_id": destino["id_destino"], "nombre": nombre},
        )
        return destino

    async def get_remito_summary(self, remito: Remito) -> Dict[str, Any]:
        """Genera un resumen del remito para mostrar al usuario."""
        return {
            "id_remito": remito.id_remito,
            "empresa": remito.nombre_empresa,
            "establecimiento": remito.nombre_establecimiento,
            "chacra": remito.nombre_chacra,
            "conductor": remito.nombre_conductor,
            "cedula": remito.cedula_conductor,
            "camion": remito.matricula_camion,
            "zorra": remito.matricula_zorra or "No aplica",
            "peso": remito.peso_estimado_tn,
            "destino": remito.nombre_destino,
            "qr_url": remito.qr_url,
            "timestamp": remito.timestamp_creacion.isoformat(),
        }
