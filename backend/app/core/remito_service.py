from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import traceback

from supabase import Client

from app.core.log_service import LogService
from app.core.qrcode_service import QRCodeService
from app.models.remito import Remito, RemitoCreate, RemitoUpdate


class RemitoService:
    """Servicio para manejar remitos persistidos en Supabase."""

    TABLE_NAME = "remitos"

    def __init__(
        self,
        supabase_client: Client,
        qrcode_service: Optional[QRCodeService] = None,
        log_service: Optional[LogService] = None,
    ) -> None:
        self.supabase = supabase_client
        self.qrcode_service = qrcode_service or QRCodeService(supabase_client)
        self.log_service = log_service

    async def list_remitos(
        self,
        activo: bool | None = None,
        destino: str | None = None,
        establecimiento: str | None = None,
        chacra: str | None = None,
        matricula_camion: str | None = None,
        matricula_zorra: str | None = None,
        cedula_conductor: str | None = None,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
    ) -> List[Remito]:
        def _list_sync() -> List[Dict[str, Any]]:
            query = self.supabase.table(self.TABLE_NAME).select("*")
            
            if activo is not None:
                query = query.eq("activo", activo)
            if destino is not None:
                query = query.or_(f"nombre_destino.ilike.%{destino}%,id_destino.eq.{destino}")
            if establecimiento is not None:
                query = query.or_(f"nombre_establecimiento.ilike.%{establecimiento}%,id_establecimiento.eq.{establecimiento}")
            if chacra is not None:
                query = query.or_(f"nombre_chacra.ilike.%{chacra}%,id_chacra.eq.{chacra}")
            if matricula_camion is not None:
                query = query.ilike("matricula_camion", f"%{matricula_camion}%")
            if matricula_zorra is not None:
                query = query.ilike("matricula_zorra", f"%{matricula_zorra}%")
            if cedula_conductor is not None:
                query = query.ilike("cedula_conductor", f"%{cedula_conductor}%")
            
            # Filtros de fecha
            if year is not None:
                query = query.gte("timestamp_creacion", f"{year}-01-01T00:00:00Z")
                query = query.lt("timestamp_creacion", f"{year + 1}-01-01T00:00:00Z")
            if month is not None:
                if year is None:
                    # Si no hay año, usar el año actual
                    from datetime import datetime
                    year = datetime.now().year
                month_str = f"{month:02d}"
                query = query.gte("timestamp_creacion", f"{year}-{month_str}-01T00:00:00Z")
                # Calcular el primer día del mes siguiente
                next_month = month + 1 if month < 12 else 1
                next_year = year if month < 12 else year + 1
                query = query.lt("timestamp_creacion", f"{next_year}-{next_month:02d}-01T00:00:00Z")
            if day is not None:
                if month is None or year is None:
                    from datetime import datetime
                    now = datetime.now()
                    year = year or now.year
                    month = month or now.month
                day_str = f"{day:02d}"
                month_str = f"{month:02d}"
                query = query.gte("timestamp_creacion", f"{year}-{month_str}-{day_str}T00:00:00Z")
                query = query.lt("timestamp_creacion", f"{year}-{month_str}-{day_str}T23:59:59Z")
            
            response = query.order("timestamp_creacion", desc=True).execute()
            return response.data or []

        records = await asyncio.to_thread(_list_sync)
        return [self._record_to_model(record) for record in records]

    async def get_remito(self, remito_id: str) -> Optional[Remito]:
        def _get_sync() -> Optional[Dict[str, Any]]:
            response = (
                self.supabase.table(self.TABLE_NAME)
                .select("*")
                .eq("id_remito", remito_id)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None

        record = await asyncio.to_thread(_get_sync)
        return self._record_to_model(record) if record else None

    async def create_remito(self, payload: RemitoCreate) -> Remito:
        timestamp = datetime.now(timezone.utc)
        remito_id = self._build_remito_id(payload.id_chacra, timestamp)
        
        if self.log_service:
            await self.log_service.write_log(
                tipo="DEBUG",
                detalle=f"Iniciando creación de remito {remito_id}",
                payload={"id_chacra": payload.id_chacra, "timestamp": timestamp.isoformat()},
            )

        try:
            # Generar QR code
            qr_url = payload.qr_url or await self.qrcode_service.generate(
                {
                    "id_remito": remito_id,
                    "nombre_establecimiento": payload.nombre_establecimiento,
                    "nombre_chacra": payload.nombre_chacra,
                    "nombre_destino": payload.nombre_destino,
                    "matricula_camion": payload.matricula_camion,
                    "matricula_zorra": payload.matricula_zorra,
                    "nombre_conductor": payload.nombre_conductor,
                    "cedula_conductor": payload.cedula_conductor,
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M"),
                },
                include_text=True,
            )

            if self.log_service:
                await self.log_service.write_log(
                    tipo="DEBUG",
                    detalle=f"QR generado para remito {remito_id}",
                    payload={"qr_url": qr_url},
                )

            remito_data = {
                **payload.model_dump(exclude={"qr_url"}),
                "id_remito": remito_id,
                "qr_url": qr_url,
                "timestamp_creacion": timestamp.isoformat(),
            }

            def _insert_sync() -> Dict[str, Any]:
                response = self.supabase.table(self.TABLE_NAME).insert(remito_data).execute()
                return response.data[0] if response.data else remito_data

            record = await asyncio.to_thread(_insert_sync)
            
            if self.log_service:
                await self.log_service.write_log(
                    tipo="DEBUG",
                    detalle=f"Remito {remito_id} insertado en Supabase",
                    payload={"record": record},
                )

            remito = self._record_to_model(record)

            if self.log_service:
                await self.log_service.write_log(
                    tipo="REMITO",
                    detalle=f"Remito creado {remito_id}",
                    payload={"id_remito": remito_id, "id_chacra": payload.id_chacra},
                )

            return remito
        except Exception as e:
            if self.log_service:
                await self.log_service.write_log(
                    tipo="ERROR",
                    detalle=f"Error creando remito {remito_id}",
                    payload={"error": str(e), "stack_trace": traceback.format_exc()},
                )
            raise

    async def update_remito(self, remito_id: str, payload: RemitoUpdate) -> Remito:
        update_data = payload.model_dump(exclude_unset=True, mode="python")
        if not update_data:
            remito = await self.get_remito(remito_id)
            if not remito:
                raise ValueError(f"Remito {remito_id} no encontrado")
            return remito

        def _update_sync() -> Optional[Dict[str, Any]]:
            response = (
                self.supabase.table(self.TABLE_NAME)
                .update(update_data)
                .eq("id_remito", remito_id)
                .execute()
            )
            return response.data[0] if response.data else None

        record = await asyncio.to_thread(_update_sync)
        if not record:
            raise ValueError(f"Remito {remito_id} no encontrado")

        if self.log_service:
            await self.log_service.write_log(
                tipo="REMITO",
                detalle=f"Remito actualizado {remito_id}",
                payload={"id_remito": remito_id, "campos": list(update_data.keys())},
            )

        return self._record_to_model(record)

    @staticmethod
    def _build_remito_id(id_chacra: str, timestamp: datetime) -> str:
        suffix = timestamp.strftime("%Y%m%d%H%M%S")
        return f"{id_chacra}-{suffix}"

    @staticmethod
    def _record_to_model(record: Dict[str, Any]) -> Remito:
        timestamp_value = record.get("timestamp_creacion")
        if isinstance(timestamp_value, str):
            timestamp_value = RemitoService._parse_datetime(timestamp_value)

        return Remito(
            id_remito=record["id_remito"],
            id_chacra=record["id_chacra"],
            nombre_chacra=record["nombre_chacra"],
            id_establecimiento=record["id_establecimiento"],
            nombre_establecimiento=record["nombre_establecimiento"],
            id_empresa=record["id_empresa"],
            nombre_empresa=record["nombre_empresa"],
            id_destino=record["id_destino"],
            nombre_destino=record["nombre_destino"],
            nombre_conductor=record["nombre_conductor"],
            cedula_conductor=record["cedula_conductor"],
            matricula_camion=record["matricula_camion"],
            matricula_zorra=record.get("matricula_zorra"),
            peso_estimado_tn=float(record["peso_estimado_tn"]),
            estado_remito=record.get("estado_remito", "despachado"),
            activo=bool(record.get("activo", True)),
            qr_url=record.get("qr_url"),
            timestamp_creacion=timestamp_value,
            raw_payload=record.get("raw_payload"),
        )

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
