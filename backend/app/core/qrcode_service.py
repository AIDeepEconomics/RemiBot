from __future__ import annotations

import asyncio
from datetime import datetime
from io import BytesIO
from typing import Any, Dict

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.image.pil import PilImage
from supabase import Client


class QRCodeService:
    """Genera códigos QR y los almacena en Supabase Storage."""

    def __init__(self, supabase_client: Client, bucket_name: str = "remibot-qrs") -> None:
        self.supabase = supabase_client
        self.bucket_name = bucket_name
        self._bucket_checked = False

    async def generate(self, payload: Dict[str, Any], include_text: bool = True) -> str:
        qr_text = self._compose_text(payload)
        storage_key = self._compose_storage_key(payload)

        # Pasar metadata para agregar texto a la imagen
        metadata = payload if include_text else None
        image_bytes = await asyncio.to_thread(self._build_qr_bytes, qr_text, metadata)
        await asyncio.to_thread(self._ensure_bucket)
        await asyncio.to_thread(self._upload_image, storage_key, image_bytes)

        return self.supabase.storage.from_(self.bucket_name).get_public_url(storage_key)

    def _build_qr_bytes(self, text: str, metadata: Dict[str, Any] = None) -> bytes:
        """Genera QR con texto informativo debajo."""
        # Generar QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(text)
        qr.make(fit=True)

        qr_image: PilImage = qr.make_image(fill_color="black", back_color="white")  # type: ignore[assignment]
        
        # Si no hay metadata, retornar solo el QR
        if not metadata:
            buffer = BytesIO()
            qr_image.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.getvalue()

        # Crear imagen con texto adicional
        qr_width, qr_height = qr_image.size
        text_height = 280  # Espacio para texto
        final_width = qr_width
        final_height = qr_height + text_height

        # Crear imagen final
        final_image = Image.new("RGB", (final_width, final_height), "white")
        final_image.paste(qr_image, (0, 0))

        # Dibujar texto
        draw = ImageDraw.Draw(final_image)
        
        # Intentar cargar fuente, si falla usar default
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except Exception:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

        # Posición inicial del texto
        y_offset = qr_height + 20

        # Título
        remito_id = metadata.get("id_remito", "")
        draw.text((20, y_offset), f"REMITO: {remito_id}", fill="black", font=font_title)
        y_offset += 35

        # Información del remito
        info_lines = [
            f"🏢 {metadata.get('nombre_establecimiento', '')} - {metadata.get('nombre_chacra', '')}",
            f"🚛 Camión: {metadata.get('matricula_camion', '')}",
        ]
        
        if metadata.get('matricula_zorra'):
            info_lines.append(f"🚛 Zorra: {metadata.get('matricula_zorra', '')}")
        
        info_lines.extend([
            f"👤 {metadata.get('nombre_conductor', '')} - CI: {metadata.get('cedula_conductor', '')}",
            f"📍 Destino: {metadata.get('nombre_destino', '')}",
            f"📅 {metadata.get('timestamp', '')}",
        ])

        for line in info_lines:
            draw.text((20, y_offset), line, fill="black", font=font_text)
            y_offset += 30

        # Guardar imagen final
        buffer = BytesIO()
        final_image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

    def _upload_image(self, key: str, data: bytes) -> None:
        self.supabase.storage.from_(self.bucket_name).upload(
            file=data,
            path=key,
            file_options={"content-type": "image/png", "upsert": True},
        )

    def _ensure_bucket(self) -> None:
        if self._bucket_checked:
            return

        buckets = self.supabase.storage.list_buckets()
        if not any(bucket.get("name") == self.bucket_name for bucket in buckets):
            # Create bucket without public parameter
            self.supabase.storage.create_bucket(self.bucket_name)
            # Make bucket public through separate API call
            self.supabase.storage.update_bucket(
                self.bucket_name,
                {"public": True}
            )

        self._bucket_checked = True

    @staticmethod
    def _compose_text(payload: Dict[str, Any]) -> str:
        return (
            f"Remito: {payload.get('id_remito', 'desconocido')}\n"
            f"Establecimiento: {payload.get('nombre_establecimiento', '-') }\n"
            f"Chacra: {payload.get('nombre_chacra', '-') }\n"
            f"Destino: {payload.get('nombre_destino', '-') }\n"
            f"Fecha: {payload.get('timestamp', datetime.utcnow().isoformat())}"
        )

    @staticmethod
    def _compose_storage_key(payload: Dict[str, Any]) -> str:
        remito_id = payload.get("id_remito")
        if not remito_id:
            remito_id = datetime.utcnow().strftime("qr-%Y%m%d%H%M%S")
        return f"remitos/{remito_id}.png"
