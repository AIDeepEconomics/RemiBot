from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.settings import get_settings

router = APIRouter()


@router.get("/supabase")
async def check_supabase_connection(settings=Depends(get_settings)):
    """
    Endpoint de diagnóstico para verificar la conexión con Supabase.
    """
    results = {
        "connection": "unknown",
        "tables": {},
        "errors": []
    }
    
    try:
        # Test 1: Verificar que el cliente existe
        if not settings.supabase_service_client:
            results["errors"].append("supabase_service_client is None")
            return results
        
        results["connection"] = "client_initialized"
        
        # Test 2: Verificar tabla logs
        try:
            response = settings.supabase_service_client.table("logs").select("*").limit(1).execute()
            results["tables"]["logs"] = {
                "exists": True,
                "count": len(response.data) if response.data else 0
            }
        except Exception as e:
            results["tables"]["logs"] = {
                "exists": False,
                "error": str(e)
            }
            results["errors"].append(f"logs table error: {str(e)}")
        
        # Test 3: Verificar tabla telefonos_empresa
        try:
            response = settings.supabase_service_client.table("telefonos_empresa").select("*").limit(1).execute()
            results["tables"]["telefonos_empresa"] = {
                "exists": True,
                "count": len(response.data) if response.data else 0
            }
        except Exception as e:
            results["tables"]["telefonos_empresa"] = {
                "exists": False,
                "error": str(e)
            }
            results["errors"].append(f"telefonos_empresa table error: {str(e)}")
        
        # Test 4: Verificar tabla empresas
        try:
            response = settings.supabase_service_client.table("empresas").select("*").limit(1).execute()
            results["tables"]["empresas"] = {
                "exists": True,
                "count": len(response.data) if response.data else 0
            }
        except Exception as e:
            results["tables"]["empresas"] = {
                "exists": False,
                "error": str(e)
            }
            results["errors"].append(f"empresas table error: {str(e)}")
        
        # Test 5: Verificar tabla remitos
        try:
            response = settings.supabase_service_client.table("remitos").select("*").limit(1).execute()
            results["tables"]["remitos"] = {
                "exists": True,
                "count": len(response.data) if response.data else 0
            }
        except Exception as e:
            results["tables"]["remitos"] = {
                "exists": False,
                "error": str(e)
            }
            results["errors"].append(f"remitos table error: {str(e)}")
        
        # Test 6: Intentar escribir un log de prueba
        try:
            await settings.log_service.write_log(
                tipo="HEALTH_CHECK",
                detalle="Test de conexión desde endpoint de diagnóstico",
                payload={"test": True}
            )
            results["log_service"] = "working"
        except Exception as e:
            results["log_service"] = f"error: {str(e)}"
            results["errors"].append(f"log_service error: {str(e)}")
        
        if len(results["errors"]) == 0:
            results["connection"] = "healthy"
        else:
            results["connection"] = "partial"
        
    except Exception as e:
        results["connection"] = "failed"
        results["errors"].append(f"General error: {str(e)}")
    
    return results
