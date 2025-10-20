-- Migración inicial para RemiBOT
-- Crea tablas base para empresas, establecimientos, chacras, destinos, remitos, configuraciones y logs.

create table if not exists empresas (
    id_empresa uuid primary key default gen_random_uuid(),
    nombre text not null
);

create table if not exists establecimientos (
    id_establecimiento uuid primary key default gen_random_uuid(),
    nombre text not null,
    id_empresa uuid not null references empresas(id_empresa) on delete cascade
);

create table if not exists chacras (
    id_chacra uuid primary key default gen_random_uuid(),
    nombre_chacra text not null,
    id_establecimiento uuid not null references establecimientos(id_establecimiento) on delete cascade,
    id_empresa uuid not null references empresas(id_empresa) on delete cascade
);

create table if not exists destinos (
    id_destino uuid primary key default gen_random_uuid(),
    nombre text not null
);

create table if not exists remitos (
    id_remito text primary key,
    id_chacra uuid not null references chacras(id_chacra) on delete restrict,
    id_destino uuid not null references destinos(id_destino) on delete restrict,
    nombre_chacra text not null,
    nombre_establecimiento text not null,
    nombre_empresa text not null,
    nombre_conductor text not null,
    cedula_conductor text not null,
    matricula_camion text not null,
    matricula_zorra text,
    peso_estimado_tn numeric(6,2) not null,
    estado_remito text not null default 'despachado',
    activo boolean not null default true,
    qr_url text,
    timestamp_creacion timestamptz not null default timezone('utc', now()),
    raw_payload jsonb
);

create table if not exists configuraciones (
    id integer primary key default 1,
    whatsapp_api_key text,
    gpt_api_key text,
    claude_api_key text,
    llm_prompt text,
    auth_password_hash text,
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists logs (
    id bigserial primary key,
    timestamp timestamptz not null default timezone('utc', now()),
    tipo text not null,
    detalle text,
    payload jsonb
);

create or replace function update_config_timestamp()
returns trigger as $$
begin
    new.updated_at := timezone('utc', now());
    return new;
end;
$$ language plpgsql;

create trigger trg_config_update
before update on configuraciones
for each row
execute function update_config_timestamp();
