#!/usr/bin/env python3
"""Test completo del flujo conversacional con LLM."""

import json
import httpx


BASE_URL = "http://localhost:8000"
CONTACT = "+598999888777"  # Nuevo contacto para historial limpio


def send_message(body: str) -> dict:
    """Envía un mensaje al webhook V2."""
    payload = {
        "from_number": CONTACT,
        "body": body,
        "message_id": f"test_{hash(body)}",
    }
    
    response = httpx.post(
        f"{BASE_URL}/webhook/whatsapp?use_v2=true",
        json=payload,
        timeout=60.0
    )
    response.raise_for_status()
    return response.json()


def main():
    print("🤖 Test completo del flujo conversacional V2\n")
    print("=" * 70)
    
    # Paso 1: Iniciar
    print("\n📱 Usuario: crear remito")
    resp = send_message("crear remito")
    print(f"🤖 RemiBOT: {resp['reply']}\n")
    
    # Paso 2: Dar toda la información de una vez
    print("📱 Usuario: (dando toda la info de una vez)")
    info = """Empresa Molino Central, establecimiento La Esperanza, chacra Norte, 
conductor Juan Pérez cédula 12345678, camión ABC1234, sin zorra, 
25 toneladas, destino Planta Procesadora Sur"""
    
    resp = send_message(info)
    print(f"🤖 RemiBOT: {resp['reply']}\n")
    
    # El LLM debería resumir y pedir confirmación
    # Paso 3: Confirmar
    print("📱 Usuario: si, confirmar")
    resp = send_message("si, confirmar")
    
    print(f"🤖 RemiBOT: {resp['reply']}")
    print(f"\n📊 Metadata:")
    print(json.dumps(resp['metadata'], indent=2))
    
    if resp['metadata'].get('status') == 'created':
        print("\n✅ ¡Remito creado exitosamente!")
        print(f"   ID: {resp['metadata'].get('id_remito')}")
        print(f"   QR URL: {resp['metadata'].get('qr_url')}")
        
        # Verificar en Supabase
        remito_id = resp['metadata'].get('id_remito')
        if remito_id:
            print(f"\n🔍 Verificando en Supabase...")
            remito_resp = httpx.get(f"{BASE_URL}/remitos/{remito_id}")
            if remito_resp.status_code == 200:
                remito = remito_resp.json()
                print(f"   ✅ Remito encontrado")
                print(f"   Empresa: {remito['nombre_empresa']}")
                print(f"   Establecimiento: {remito['nombre_establecimiento']}")
                print(f"   Chacra: {remito['nombre_chacra']}")
                print(f"   Conductor: {remito['nombre_conductor']} - CI: {remito['cedula_conductor']}")
                print(f"   Camión: {remito['matricula_camion']}")
                print(f"   Peso: {remito['peso_estimado_tn']} tn")
                print(f"   Destino: {remito['nombre_destino']}")
                print(f"   Timestamp: {remito['timestamp_creacion']}")
                print(f"   QR: {remito['qr_url']}")
            else:
                print(f"   ❌ Error: {remito_resp.status_code}")
    else:
        print(f"\n⚠️  Estado: {resp['metadata'].get('status')}")
        if resp['metadata'].get('status') == 'conversation':
            print("   El LLM está pidiendo más información o confirmación")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
