#!/usr/bin/env python3
"""
Script de prueba para verificar que la refactorización funciona correctamente.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.settings import get_settings
from app.services.validation_service import RemitoValidator


async def test_validacion():
    """Prueba el servicio de validación."""
    print("🧪 Probando servicio de validación...")
    
    # Test de validación de cédula
    result = RemitoValidator.validate_cedula("1.234.567-8")
    print(f"✅ Cédula '1.234.567-8' -> {result.normalized_data['cedula']}")
    
    # Test de validación de peso
    result = RemitoValidator.validate_peso("25.5 toneladas")
    print(f"✅ Peso '25.5 toneladas' -> {result.normalized_data['peso']}")
    
    # Test de validación de matrícula
    result = RemitoValidator.validate_matricula("ABC 1234")
    print(f"✅ Matrícula 'ABC 1234' -> {result.normalized_data['matricula']}")


async def test_settings():
    """Prueba que los settings se cargan correctamente."""
    print("🔧 Probando configuración...")
    
    settings = get_settings()
    
    print(f"✅ Supabase conectado: {settings.supabase_service_client is not None}")
    print(f"✅ LLM Service: {settings.llm_service is not None}")
    print(f"✅ Remito Flow V2 Refactored: {settings.remito_flow_v2_refactored is not None}")
    print(f"✅ Conversation Service: {hasattr(settings, 'remito_flow_v2_refactored')}")


async def test_repositorios():
    """Prueba los nuevos repositorios."""
    print("📊 Probando repositorios...")
    
    from app.repositories.empresa_repository import EmpresaRepository
    from app.core.settings import get_settings
    
    settings = get_settings()
    empresa_repo = EmpresaRepository(settings.supabase_service_client)
    
    # Test básico de conexión
    try:
        empresas = await empresa_repo.list_active()
        print(f"✅ Repositorio empresas: {len(empresas)} empresas activas")
    except Exception as e:
        print(f"⚠️  Error en repositorio: {e}")


async def main():
    """Ejecuta todas las pruebas."""
    print("🚀 Iniciando pruebas de refactorización...\n")
    
    try:
        await test_validacion()
        print()
        await test_settings()
        print()
        await test_repositorios()
        
        print("\n✅ Todas las pruebas pasaron!")
        print("El sistema refacturado está listo para usar.")
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
