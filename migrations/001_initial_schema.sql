-- ==============================================================================
-- Migration: 001_initial_schema.sql
-- Description: Core schema for Career Fit Jobs Bot.
-- Includes users, profiles, job listings, application tracking, job suggestions,
-- and scraper state. Follows Supabase/Postgres best practices.
-- ==============================================================================

-- Enable extensions if needed
create extension if not exists "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. Users Table
-- ------------------------------------------------------------------------------
create table if not exists users (
    id bigint generated always as identity primary key,
    telegram_id bigint not null,
    preferences text[] not null default '{}',
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_users_telegram_id unique (telegram_id)
);

create index if not exists idx_users_telegram_id on users (telegram_id);
create index if not exists idx_users_preferences on users using gin (preferences);

-- ------------------------------------------------------------------------------
-- 2. User Profiles Table (1:1 with users)
-- Stores CV path (Supabase Storage), experience, and skills
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 3. Job Listings Table
-- Scraped job posts from monitored Telegram channels
-- ------------------------------------------------------------------------------
create table if not exists job_listings (
    id bigint generated always as identity primary key,
    channel text not null,
    message_id bigint not null,
    message_link text not null,
    summary text not null,
    raw_text text,
    scraped_at timestamptz not null default now(),
    constraint uq_job_listings_channel_message unique (channel, message_id)
);

create index if not exists idx_job_listings_scraped_at on job_listings (scraped_at desc);
create index if not exists idx_job_listings_channel on job_listings (channel);

-- ------------------------------------------------------------------------------
-- 4. Applications Table
-- Application tracking by link
-- ------------------------------------------------------------------------------
create table if not exists applications (
    id bigint generated always as identity primary key,
    user_id bigint not null references users(id) on delete cascade,
    job_link text not null,
    status text not null default 'applied'
        check (status in ('applied', 'interviewing', 'offered', 'rejected', 'withdrawn')),
    cv_storage_path text,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_applications_user_id on applications (user_id);
create index if not exists idx_applications_status on applications (status);

-- ------------------------------------------------------------------------------
-- 5. Job Suggestions Table
-- User-suggested jobs queued for admin review
-- ------------------------------------------------------------------------------
create table if not exists job_suggestions (
    id bigint generated always as identity primary key,
    submitted_by bigint not null references users(id) on delete cascade,
    job_link text not null,
    status text not null default 'pending'
        check (status in ('pending', 'approved', 'rejected')),
    review_notes text,
    reviewed_by bigint references users(id) on delete set null,
    created_at timestamptz not null default now(),
    reviewed_at timestamptz
);

create index if not exists idx_job_suggestions_submitted_by on job_suggestions (submitted_by);
create index if not exists idx_job_suggestions_status on job_suggestions (status);

-- ------------------------------------------------------------------------------
-- 6. Scraper State Table
-- Tracks per-channel scraping watermark (replaces local last_scrape.txt)
-- ------------------------------------------------------------------------------
create table if not exists scraper_state (
    channel text primary key,
    last_message_id bigint not null default 0,
    last_scraped_at timestamptz not null default now()
);

-- ------------------------------------------------------------------------------
-- Row-Level Security (RLS)
-- ------------------------------------------------------------------------------
alter table users enable row level security;
alter table user_profiles enable row level security;
alter table job_listings enable row level security;
alter table applications enable row level security;
alter table job_suggestions enable row level security;
alter table scraper_state enable row level security;

-- Default policies: allow service role full access; anon read-only where appropriate
-- Service role bypasses RLS in Supabase, but policies ensure clarity for direct access
do $$
begin
    -- users table policies
    if not exists (select 1 from pg_policies where policyname = 'allow_service_role_all_users') then
        create policy allow_service_role_all_users on users
            for all to service_role using (true) with check (true);
    end if;

    -- user_profiles table policies
    if not exists (select 1 from pg_policies where policyname = 'allow_service_role_all_profiles') then
        create policy allow_service_role_all_profiles on user_profiles
            for all to service_role using (true) with check (true);
    end if;

    -- job_listings table policies
    if not exists (select 1 from pg_policies where policyname = 'allow_service_role_all_jobs') then
        create policy allow_service_role_all_jobs on job_listings
            for all to service_role using (true) with check (true);
    end if;

    -- applications table policies
    if not exists (select 1 from pg_policies where policyname = 'allow_service_role_all_applications') then
        create policy allow_service_role_all_applications on applications
            for all to service_role using (true) with check (true);
    end if;

    -- job_suggestions table policies
    if not exists (select 1 from pg_policies where policyname = 'allow_service_role_all_suggestions') then
        create policy allow_service_role_all_suggestions on job_suggestions
            for all to service_role using (true) with check (true);
    end if;

    -- scraper_state table policies
    if not exists (select 1 from pg_policies where policyname = 'allow_service_role_all_scraper_state') then
        create policy allow_service_role_all_scraper_state on scraper_state
            for all to service_role using (true) with check (true);
    end if;
end $$;
