#!/usr/bin/env python3
"""
Script para probar el flujo conversacional V2 con LLM y generación de QR.
"""

import json
import httpx


BASE_URL = "http://localhost:8000"
CONTACT = "+598123456789"


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
    print("🤖 Probando flujo conversacional V2 con LLM\n")
    print("=" * 70)
    
    # Paso 1: Saludo inicial
    print("\n📱 Usuario: Hola, quiero crear un remito")
    resp = send_message("Hola, quiero crear un remito")
    print(f"🤖 RemiBOT: {resp['reply']}\n")
    
    # Paso 2: Dar toda la información de una vez
    print("📱 Usuario: (dando toda la info)")
    mensaje_completo = """La empresa es Molino Central, 
establecimiento La Esperanza, 
chacra Norte, 
conductor Juan Pérez con cédula 12345678, 
camión ABC1234, 
sin zorra, 
peso 25 toneladas, 
destino Planta Procesadora Sur"""
    
    resp = send_message(mensaje_completo)
    print(f"🤖 RemiBOT: {resp['reply']}\n")
    
    # Paso 3: Confirmar
    print("📱 Usuario: confirmar")
    resp = send_message("confirmar")
    
    print(f"🤖 RemiBOT: {resp['reply']}")
    print(f"\n📊 Metadata: {json.dumps(resp['metadata'], indent=2)}")
    
    if resp['metadata'].get('status') == 'created':
        print("\n✅ ¡Remito creado exitosamente!")
        print(f"   ID: {resp['metadata'].get('id_remito')}")
        print(f"   QR URL: {resp['metadata'].get('qr_url')}")
        print(f"   Imagen enviada por WhatsApp: {resp['metadata'].get('image_sent')}")
        
        # Verificar en la base de datos
        remito_id = resp['metadata'].get('id_remito')
        if remito_id:
            print(f"\n🔍 Verificando remito en la base de datos...")
            remito_resp = httpx.get(f"{BASE_URL}/remitos/{remito_id}")
            if remito_resp.status_code == 200:
                remito = remito_resp.json()
                print(f"   ✅ Remito encontrado en Supabase")
                print(f"   Empresa: {remito['nombre_empresa']}")
                print(f"   Establecimiento: {remito['nombre_establecimiento']}")
                print(f"   Chacra: {remito['nombre_chacra']}")
                print(f"   Conductor: {remito['nombre_conductor']}")
                print(f"   Peso: {remito['peso_estimado_tn']} tn")
                print(f"   Timestamp: {remito['timestamp_creacion']}")
                print(f"   QR URL: {remito['qr_url']}")
            else:
                print(f"   ❌ Error al verificar remito: {remito_resp.status_code}")
    else:
        print(f"\n⚠️  Estado: {resp['metadata'].get('status')}")
    
    print("\n" + "=" * 70)
    print("✅ Prueba completada")


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as e:
        print(f"\n❌ Error de conexión: {e}")
        import traceback
        traceback.print_exc()
    except KeyboardInterrupt:
        print("\n\n⚠️  Prueba interrumpida")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
