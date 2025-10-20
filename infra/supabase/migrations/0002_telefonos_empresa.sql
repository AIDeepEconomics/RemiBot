-- Migración: Tabla de teléfonos asociados a empresas
-- Permite múltiples números por empresa y un número en múltiples empresas

CREATE TABLE IF NOT EXISTS telefonos_empresa (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  numero_telefono VARCHAR(20) NOT NULL,
  numero_normalizado VARCHAR(20) NOT NULL,
  id_empresa uuid NOT NULL REFERENCES empresas(id_empresa) ON DELETE CASCADE,
  activo BOOLEAN DEFAULT true,
  notas TEXT,
  created_at TIMESTAMPTZ DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ DEFAULT timezone('utc', now())
);

-- Índices para búsqueda rápida
CREATE INDEX idx_telefonos_normalizado ON telefonos_empresa(numero_normalizado) WHERE activo = true;
CREATE INDEX idx_telefonos_empresa_id ON telefonos_empresa(id_empresa) WHERE activo = true;

-- Trigger para auto-actualizar updated_at
CREATE OR REPLACE FUNCTION update_telefonos_empresa_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_telefonos_empresa_timestamp
BEFORE UPDATE ON telefonos_empresa
FOR EACH ROW
EXECUTE FUNCTION update_telefonos_empresa_timestamp();

-- Función para normalizar números de teléfono
CREATE OR REPLACE FUNCTION normalize_phone_number(phone TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Eliminar todos los caracteres no numéricos
    RETURN regexp_replace(phone, '[^0-9]', '', 'g');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger para auto-normalizar número al insertar/actualizar
CREATE OR REPLACE FUNCTION normalize_phone_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.numero_normalizado = normalize_phone_number(NEW.numero_telefono);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_normalize_phone
BEFORE INSERT OR UPDATE ON telefonos_empresa
FOR EACH ROW
EXECUTE FUNCTION normalize_phone_trigger();

-- Comentarios para documentación
COMMENT ON TABLE telefonos_empresa IS 'Números de teléfono autorizados por empresa para usar RemiBOT';
COMMENT ON COLUMN telefonos_empresa.numero_telefono IS 'Número original como fue ingresado';
COMMENT ON COLUMN telefonos_empresa.numero_normalizado IS 'Número sin caracteres especiales para búsqueda';
COMMENT ON COLUMN telefonos_empresa.activo IS 'Si false, el número no puede crear remitos';
