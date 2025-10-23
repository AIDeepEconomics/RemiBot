from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Resultado de una validación."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    normalized_data: Optional[Dict[str, Any]] = None

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class RemitoValidator:
    """Servicio centralizado para validar datos de remitos."""

    # Patrones de validación
    CEDULA_PATTERN = re.compile(r'^\d{7,10}$')
    MATRICULA_URUGUAY = re.compile(r'^[A-Z]{3}\s?\d{4}$')
    MATRICULA_ARGENTINA = re.compile(r'^[A-Z]{2}\s?\d{3}\s?[A-Z]{2}$')
    MATRICULA_BRASIL = re.compile(r'^[A-Z]{3}\d[A-Z]\d{2}$')
    MATRICULA_PARAGUAY = re.compile(r'^[A-Z]{4}\s?\d{3}$')
    
    # Rangos válidos
    MIN_PESO_TONELADAS = 5.0
    MAX_PESO_TONELADAS = 40.0

    @staticmethod
    def validate_json_remito(data: Dict[str, Any]) -> ValidationResult:
        """Valida el JSON completo de un remito."""
        errors = []
        warnings = []
        normalized_data = {}

        # Campos requeridos
        required_fields = {
            'nombre_empresa': 'Empresa',
            'nombre_establecimiento': 'Establecimiento',
            'nombre_chacra': 'Chacra',
            'nombre_conductor': 'Conductor',
            'cedula_conductor': 'Cédula',
            'matricula_camion': 'Matrícula camión',
            'peso_estimado_tn': 'Peso estimado',
            'nombre_destino': 'Destino'
        }

        # Validar campos requeridos
        for field, label in required_fields.items():
            if field not in data or data[field] is None or str(data[field]).strip() == '':
                errors.append(f"{label} es requerido")
            else:
                normalized_data[field] = str(data[field]).strip()

        # Validaciones específicas
        if 'cedula_conductor' in normalized_data:
            cedula_result = RemitoValidator.validate_cedula(normalized_data['cedula_conductor'])
            if cedula_result.has_errors:
                errors.extend(cedula_result.errors)
            else:
                normalized_data['cedula_conductor'] = cedula_result.normalized_data['cedula']

        if 'matricula_camion' in normalized_data:
            matricula_result = RemitoValidator.validate_matricula(normalized_data['matricula_camion'])
            if matricula_result.has_errors:
                errors.extend(matricula_result.errors)
            else:
                normalized_data['matricula_camion'] = matricula_result.normalized_data['matricula']

        if 'matricula_zorra' in normalized_data:
            zorra_value = normalized_data['matricula_zorra']
            if zorra_value and zorra_value.lower() not in ['null', 'ninguna', 'no tiene', 'sin zorra']:
                zorra_result = RemitoValidator.validate_matricula(zorra_value)
                if zorra_result.has_errors:
                    warnings.append(f"Matrícula zorra: {zorra_result.errors[0]}")
                else:
                    normalized_data['matricula_zorra'] = zorra_result.normalized_data['matricula']
            else:
                normalized_data['matricula_zorra'] = None

        if 'peso_estimado_tn' in normalized_data:
            peso_result = RemitoValidator.validate_peso(normalized_data['peso_estimado_tn'])
            if peso_result.has_errors:
                errors.extend(peso_result.errors)
            else:
                normalized_data['peso_estimado_tn'] = peso_result.normalized_data['peso']

        # Validar nombres no estén vacíos
        for field in ['nombre_empresa', 'nombre_establecimiento', 'nombre_chacra', 'nombre_conductor', 'nombre_destino']:
            if field in normalized_data and len(normalized_data[field]) < 2:
                errors.append(f"{required_fields[field]} debe tener al menos 2 caracteres")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_data=normalized_data if len(errors) == 0 else None
        )

    @staticmethod
    def validate_cedula(cedula: str) -> ValidationResult:
        """Valida y normaliza una cédula uruguaya."""
        errors = []
        
        # Limpiar la cédula
        cleaned = re.sub(r'[^\d]', '', str(cedula))
        
        if not cleaned:
            errors.append("Cédula no puede estar vacía")
        elif not RemitoValidator.CEDULA_PATTERN.match(cleaned):
            errors.append("Cédula debe tener entre 7 y 10 dígitos")
        elif len(cleaned) < 7:
            errors.append("Cédula muy corta")
        elif len(cleaned) > 10:
            errors.append("Cédula muy larga")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[],
            normalized_data={'cedula': cleaned} if len(errors) == 0 else None
        )

    @staticmethod
    def validate_matricula(matricula: str) -> ValidationResult:
        """Valida y normaliza una matrícula de vehículo."""
        errors = []
        cleaned = str(matricula).strip().upper()
        
        # Limpiar espacios
        cleaned = re.sub(r'\s+', '', cleaned)
        
        patterns = [
            RemitoValidator.MATRICULA_URUGUAY,
            RemitoValidator.MATRICULA_ARGENTINA,
            RemitoValidator.MATRICULA_BRASIL,
            RemitoValidator.MATRICULA_PARAGUAY
        ]
        
        is_valid = any(pattern.match(cleaned) for pattern in patterns)
        
        if not is_valid:
            errors.append(
                "Matrícula inválida. Formatos válidos: ABC1234 (UY), AB123CD (AR), ABC1D23 (BR), ABCD123 (PY)"
            )

        # Normalizar agregando espacio si es uruguaya o paraguaya
        normalized = cleaned
        if RemitoValidator.MATRICULA_URUGUAY.match(cleaned):
            normalized = f"{cleaned[:3]} {cleaned[3:]}"
        elif RemitoValidator.MATRICULA_PARAGUAY.match(cleaned):
            normalized = f"{cleaned[:4]} {cleaned[4:]}"

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[],
            normalized_data={'matricula': normalized} if len(errors) == 0 else None
        )

    @staticmethod
    def validate_peso(peso: Any) -> ValidationResult:
        """Valida y normaliza el peso estimado."""
        errors = []
        
        try:
            # Convertir a float
            if isinstance(peso, str):
                # Manejar casos como "25.5 toneladas" o "25000 kg"
                cleaned = re.sub(r'[^\d.,]', '', str(peso))
                cleaned = cleaned.replace(',', '.')
                peso_float = float(cleaned)
                
                # Si está en kg, convertir a toneladas
                if 'kg' in str(peso).lower() and 'tonelada' not in str(peso).lower():
                    peso_float = peso_float / 1000
            else:
                peso_float = float(peso)
            
            # Validar rango
            if peso_float < RemitoValidator.MIN_PESO_TONELADAS:
                errors.append(f"Peso mínimo: {RemitoValidator.MIN_PESO_TONELADAS} toneladas")
            elif peso_float > RemitoValidator.MAX_PESO_TONELADAS:
                errors.append(f"Peso máximo: {RemitoValidator.MAX_PESO_TONELADAS} toneladas")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=[],
                normalized_data={'peso': round(peso_float, 2)} if len(errors) == 0 else None
            )
            
        except (ValueError, TypeError):
            errors.append("Peso debe ser un número válido")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=[],
                normalized_data=None
            )

    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """Normaliza un número de teléfono."""
        if not phone:
            return ""
            
        # Eliminar todo excepto dígitos
        cleaned = re.sub(r'[^\d+]', '', str(phone))
        
        # Si empieza con +, mantenerlo
        if str(phone).startswith('+'):
            cleaned = '+' + re.sub(r'[^\d]', '', str(phone))
        
        return cleaned

    @staticmethod
    def validate_phone_number(phone: str) -> ValidationResult:
        """Valida un número de teléfono."""
        errors = []
        
        normalized = RemitoValidator.normalize_phone_number(phone)
        
        if not normalized:
            errors.append("Número de teléfono no puede estar vacío")
        elif len(normalized.replace('+', '')) < 8:
            errors.append("Número de teléfono muy corto")
        elif len(normalized.replace('+', '')) > 15:
            errors.append("Número de teléfono muy largo")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[],
            normalized_data={'phone': normalized} if len(errors) == 0 else None
        )

    @staticmethod
    def validate_nombre(nombre: str, min_length: int = 2) -> ValidationResult:
        """Valida un nombre."""
        errors = []
        
        cleaned = str(nombre).strip()
        
        if not cleaned:
            errors.append("Nombre no puede estar vacío")
        elif len(cleaned) < min_length:
            errors.append(f"Nombre debe tener al menos {min_length} caracteres")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[],
            normalized_data={'nombre': cleaned} if len(errors) == 0 else None
        )
