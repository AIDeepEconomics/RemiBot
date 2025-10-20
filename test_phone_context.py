#!/usr/bin/env python3
"""
Test del sistema de contexto personalizado por teléfono.
"""

import httpx
import asyncio


BASE_URL = "http://localhost:8000"


async def setup_test_data():
    """Inserta datos de prueba: empresa, establecimiento, chacra y teléfono."""
    print("🔧 Configurando datos de prueba...\n")
    
    # 1. Crear empresa de prueba
    print("1. Creando empresa 'Molino Test'...")
    empresa_data = {"nombre_empresa": "Molino Test"}
    
    async with httpx.AsyncClient() as client:
        # Verificar si ya existe
        response = await client.get(f"{BASE_URL}/empresas")
        empresas = response.json() if response.status_code == 200 else []
        
        empresa_test = next((e for e in empresas if e['nombre_empresa'] == 'Molino Test'), None)
        
        if not empresa_test:
            # Crear directamente en Supabase usando el endpoint de catálogo
            # Por ahora usaremos un ID conocido o crearemos manualmente
            print("   ⚠️  Necesitas crear la empresa manualmente en Supabase")
            print("   Ejecuta: INSERT INTO empresas (nombre_empresa) VALUES ('Molino Test');")
            return None
        
        empresa_id = empresa_test['id_empresa']
        print(f"   ✅ Empresa ID: {empresa_id}")
        
        # 2. Registrar teléfono de prueba
        print("\n2. Registrando teléfono +598 99 123 456...")
        telefono_data = {
            "numero_telefono": "+598 99 123 456",
            "id_empresa": empresa_id,
            "notas": "Teléfono de prueba para testing"
        }
        
        response = await client.post(f"{BASE_URL}/telefonos", json=telefono_data)
        if response.status_code == 201:
            telefono = response.json()
            print(f"   ✅ Teléfono registrado: {telefono['numero_normalizado']}")
        else:
            print(f"   ⚠️  Error: {response.text}")
        
        # 3. Verificar que el teléfono está asociado
        print("\n3. Verificando asociación...")
        response = await client.get(f"{BASE_URL}/telefonos/check/+598 99 123 456")
        if response.status_code == 200:
            empresas_asociadas = response.json()
            print(f"   ✅ Empresas asociadas: {empresas_asociadas}")
        
        return empresa_id


async def test_registered_phone():
    """Prueba con un número registrado."""
    print("\n" + "="*70)
    print("📱 TEST 1: Número REGISTRADO (+598 99 123 456)")
    print("="*70 + "\n")
    
    payload = {
        "from_number": "+598 99 123 456",
        "body": "crear remito",
        "message_id": "test_registered_001",
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/webhook/whatsapp?use_v2=true",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 RemiBOT: {data['reply']}\n")
            print(f"📊 Metadata: {data['metadata']}")
            
            # Verificar que el prompt incluye contexto de empresa
            if "empresa" in data['reply'].lower() or "establecimiento" in data['reply'].lower():
                print("\n✅ El LLM recibió contexto de empresa")
            else:
                print("\n⚠️  El LLM NO parece tener contexto de empresa")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")


async def test_unregistered_phone():
    """Prueba con un número NO registrado."""
    print("\n" + "="*70)
    print("📱 TEST 2: Número NO REGISTRADO (+598 91 999 999)")
    print("="*70 + "\n")
    
    payload = {
        "from_number": "+598 91 999 999",
        "body": "hola, quiero crear un remito",
        "message_id": "test_unregistered_001",
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/webhook/whatsapp?use_v2=true",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 RemiBOT: {data['reply']}\n")
            print(f"📊 Metadata: {data['metadata']}")
            
            # Verificar que el LLM explica que no está registrado
            if "registrado" in data['reply'].lower() or "autorizado" in data['reply'].lower():
                print("\n✅ El LLM explicó que el número no está registrado")
            else:
                print("\n⚠️  El LLM NO explicó la situación correctamente")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")


async def test_phone_normalization():
    """Prueba la normalización de números."""
    print("\n" + "="*70)
    print("🔧 TEST 3: Normalización de Números")
    print("="*70 + "\n")
    
    test_numbers = [
        "+598 99 123 456",
        "099 123 456",
        "59899123456",
        "(598) 99-123-456",
    ]
    
    async with httpx.AsyncClient() as client:
        for numero in test_numbers:
            response = await client.get(f"{BASE_URL}/telefonos/check/{numero}")
            if response.status_code == 200:
                empresas = response.json()
                print(f"   {numero:20} → Empresas: {empresas}")


async def main():
    print("🤖 Test del Sistema de Contexto Personalizado por Teléfono\n")
    
    try:
        # Setup
        empresa_id = await setup_test_data()
        
        if empresa_id is None:
            print("\n⚠️  Necesitas configurar datos de prueba primero")
            print("   Crea una empresa en Supabase y vuelve a ejecutar este script")
            return
        
        # Tests
        await test_registered_phone()
        await test_unregistered_phone()
        await test_phone_normalization()
        
        print("\n" + "="*70)
        print("✅ Tests completados")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
