-- ------------------------------------------------------------------------------
-- Migration 002: Add work_type (Remote, Hybrid, On-site) and ensure profile schema
-- ------------------------------------------------------------------------------

-- 1. Add work_type to job_listings
alter table job_listings
add column if not exists work_type text not null default 'Unspecified';

create index if not exists idx_job_listings_work_type on job_listings (work_type);

-- 2. Ensure user_profiles table structure and constraints
create table if not exists user_profiles (
    id bigint generated always as identity primary key,
    user_id bigint not null references users(id) on delete cascade,
    cv_storage_path text,
    cv_original_filename text,
    skills text,
    experience text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_user_profiles_user_id unique (user_id)
);

create index if not exists idx_user_profiles_user_id on user_profiles (user_id);

-- Enable RLS and service role access
alter table user_profiles enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies where tablename = 'user_profiles' and policyname = 'allow_service_role_all_profiles'
    ) then
        create policy allow_service_role_all_profiles on user_profiles
            for all to service_role using (true) with check (true);
    end if;
end $$;
