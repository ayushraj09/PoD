create extension if not exists vector;
create extension if not exists pgcrypto;

create table waitlists (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id),
  slug text unique not null,
  product_name text not null,
  product_description text,          -- used by the AI pain scorer as context
  question text not null,            -- the voice question shown to signups
  deposit_enabled boolean not null default false,
  deposit_amount_cents int not null default 100,
  deposit_currency text not null default 'USD',
  created_at timestamptz not null default now()
);

create table signups (
  id uuid primary key default gen_random_uuid(),
  waitlist_id uuid not null references waitlists(id) on delete cascade,
  email text not null,
  consent boolean not null default false,
  audio_path text,                   -- path in Supabase Storage bucket "audio"
  device_id text,                    -- FingerprintJS visitor id from the widget
  ip_hash text,                      -- salted hash, never the raw IP
  user_agent text,
  -- written by A (backend)
  status text not null default 'pending',      -- pending | processing | scored | failed
  transcript text,
  language text,
  pain_score int,                    -- 0-100
  pain_reason text,
  pain_quote text,
  human_verdict text,                -- verified | suspicious | fake | unverified
  flags jsonb not null default '[]'::jsonb,
  trust_score int,                   -- 0-100
  voice_embedding vector(192),
  -- written by B (web, from Dodo webhook)
  deposit_status text not null default 'none',  -- none | pending | paid | refunded
  deposit_payment_id text,
  created_at timestamptz not null default now(),
  unique (waitlist_id, email)
);

create index on signups (waitlist_id, created_at desc);
create index on signups (waitlist_id, device_id);
create index on signups (waitlist_id, ip_hash);
