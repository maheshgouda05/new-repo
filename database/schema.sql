-- ==============================================================================
-- ANALYTIX CLUB DATABASE SCHEMA (PostgreSQL / Supabase)
-- ==============================================================================
-- This schema configures all tables, constraints, indexes, triggers,
-- Row Level Security (RLS) policies, and storage bucket definitions for
-- the Analytix Club website.
-- ==============================================================================

-- 1. Enable UUID Extension (standard in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- TABLE 1: profiles
-- Linked to Supabase Auth (auth.users)
-- Stores user identity, contact, team assignment, and system role (admin/member)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT DEFAULT '',
    profile_photo TEXT DEFAULT '',
    department TEXT DEFAULT '',
    year TEXT DEFAULT '',
    skills TEXT DEFAULT '',
    bio TEXT DEFAULT '',
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member')),
    team TEXT NOT NULL DEFAULT 'None' CHECK (team IN ('None', 'Tech', 'Design', 'MOC')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for quick lookup by email and role
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_team ON public.profiles(team);

-- ==============================================================================
-- TABLE 2: events
-- Club events, workshops, guest lectures, bootcamps
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    poster_url TEXT DEFAULT '',
    photos TEXT[] DEFAULT '{}',
    event_date TIMESTAMPTZ NOT NULL,
    venue TEXT NOT NULL,
    registration_deadline TIMESTAMPTZ NOT NULL,
    instructions TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published', 'completed', 'cancelled')),
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_status ON public.events(status);
CREATE INDEX IF NOT EXISTS idx_events_date ON public.events(event_date);

-- ==============================================================================
-- TABLE 3: hackathons
-- Internal and external hackathons curated for club members
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.hackathons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    organizer TEXT NOT NULL,
    description TEXT NOT NULL,
    poster_url TEXT DEFAULT '',
    start_date TIMESTAMPTZ NOT NULL,
    deadline TIMESTAMPTZ NOT NULL,
    location TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'online' CHECK (mode IN ('online', 'offline', 'hybrid')),
    registration_link TEXT DEFAULT '',
    eligibility TEXT NOT NULL DEFAULT 'All college students',
    required_skills TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published', 'completed', 'cancelled')),
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hackathons_status ON public.hackathons(status);
CREATE INDEX IF NOT EXISTS idx_hackathons_deadline ON public.hackathons(deadline);

-- ==============================================================================
-- TABLE 4: announcements
-- Official notices, updates, and news for club members
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.announcements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    image_url TEXT DEFAULT '',
    category TEXT NOT NULL DEFAULT 'General' CHECK (category IN ('General', 'Notice', 'Urgent', 'Opportunity', 'Event')),
    status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_announcements_status ON public.announcements(status);

-- ==============================================================================
-- TABLE 5: registrations (Event Registrations)
-- Tracks member applications for club events
-- Prevents duplicate registrations with UNIQUE constraint
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'attended')),
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_member_event_registration UNIQUE (member_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_registrations_member ON public.registrations(member_id);
CREATE INDEX IF NOT EXISTS idx_registrations_event ON public.registrations(event_id);

-- ==============================================================================
-- TABLE 6: hackathon_registrations (Internal Hackathon Applications)
-- Tracks member registrations or team participation for hackathons
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.hackathon_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    hackathon_id UUID NOT NULL REFERENCES public.hackathons(id) ON DELETE CASCADE,
    team_name TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'registered' CHECK (status IN ('registered', 'shortlisted', 'participated', 'winner')),
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_member_hackathon_registration UNIQUE (member_id, hackathon_id)
);

CREATE INDEX IF NOT EXISTS idx_hackathon_registrations_member ON public.hackathon_registrations(member_id);
CREATE INDEX IF NOT EXISTS idx_hackathon_registrations_hackathon ON public.hackathon_registrations(hackathon_id);

-- ==============================================================================
-- TABLE 7: leaderboard
-- Points and activities awarded to club members by admins
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.leaderboard (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    points INTEGER NOT NULL CHECK (points >= 0),
    activity_description TEXT NOT NULL,
    awarded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_member ON public.leaderboard(member_id);

-- ==============================================================================
-- TRIGGER 1: Automatically create a profile entry when a user signs up via Supabase Auth
-- ==============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (
        id,
        email,
        full_name,
        phone,
        department,
        year,
        skills,
        bio,
        role,
        team
    ) VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'phone', ''),
        COALESCE(NEW.raw_user_meta_data->>'department', ''),
        COALESCE(NEW.raw_user_meta_data->>'year', ''),
        COALESCE(NEW.raw_user_meta_data->>'skills', ''),
        COALESCE(NEW.raw_user_meta_data->>'bio', ''),
        -- Safety: All signups default to member! Role can only be changed by an existing admin.
        'member',
        'None'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==============================================================================
-- TRIGGER 2: Auto-update updated_at timestamp on row modification
-- ==============================================================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS trg_events_updated_at ON public.events;
CREATE TRIGGER trg_events_updated_at BEFORE UPDATE ON public.events FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS trg_hackathons_updated_at ON public.hackathons;
CREATE TRIGGER trg_hackathons_updated_at BEFORE UPDATE ON public.hackathons FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS trg_announcements_updated_at ON public.announcements;
CREATE TRIGGER trg_announcements_updated_at BEFORE UPDATE ON public.announcements FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ==============================================================================
-- VIEW: Leaderboard Summary
-- Aggregates total points and completed activities for each member
-- ==============================================================================
CREATE OR REPLACE VIEW public.leaderboard_summary AS
SELECT 
    p.id AS member_id,
    p.full_name,
    p.email,
    p.department,
    p.year,
    p.team,
    p.profile_photo,
    COALESCE(SUM(l.points), 0)::INT AS total_points,
    COUNT(l.id)::INT AS activities_count,
    DENSE_RANK() OVER (ORDER BY COALESCE(SUM(l.points), 0) DESC) AS rank
FROM public.profiles p
LEFT JOIN public.leaderboard l ON p.id = l.member_id
WHERE p.role = 'member' OR p.role = 'admin'
GROUP BY p.id, p.full_name, p.email, p.department, p.year, p.team, p.profile_photo
ORDER BY total_points DESC, p.full_name ASC;

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hackathons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hackathon_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leaderboard ENABLE ROW LEVEL SECURITY;

-- Helper function: Check if current authenticated user is an admin
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid() AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- --- PROFILES POLICIES ---
-- Any authenticated user can view profiles
CREATE POLICY "Profiles are viewable by authenticated users"
    ON public.profiles FOR SELECT
    TO authenticated
    USING (true);

-- Members can only update their own profile, but CANNOT touch role or team
CREATE POLICY "Users can update their own permitted profile fields"
    ON public.profiles FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (
        auth.uid() = id AND
        -- Ensure member cannot change their own role or team directly
        (public.is_admin() OR (role = (SELECT role FROM public.profiles WHERE id = auth.uid()) AND team = (SELECT team FROM public.profiles WHERE id = auth.uid())))
    );

-- Admins can update any profile (e.g., assign team, change role)
CREATE POLICY "Admins can update any profile"
    ON public.profiles FOR UPDATE
    TO authenticated
    USING (public.is_admin());

-- --- EVENTS POLICIES ---
-- Everyone can read published events; Admins can read all events (including drafts)
CREATE POLICY "Read published events or admin access"
    ON public.events FOR SELECT
    TO public
    USING (status = 'published' OR status = 'completed' OR public.is_admin());

-- Only admins can create, update, or delete events
CREATE POLICY "Admins can manage events"
    ON public.events FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- --- HACKATHONS POLICIES ---
-- Everyone can read published hackathons; Admins can read all
CREATE POLICY "Read published hackathons or admin access"
    ON public.hackathons FOR SELECT
    TO public
    USING (status = 'published' OR status = 'completed' OR public.is_admin());

CREATE POLICY "Admins can manage hackathons"
    ON public.hackathons FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- --- ANNOUNCEMENTS POLICIES ---
CREATE POLICY "Read published announcements or admin access"
    ON public.announcements FOR SELECT
    TO public
    USING (status = 'published' OR public.is_admin());

CREATE POLICY "Admins can manage announcements"
    ON public.announcements FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- --- REGISTRATIONS POLICIES ---
-- Members can view their own registrations; Admins can view all
CREATE POLICY "Members view own registrations, admins view all"
    ON public.registrations FOR SELECT
    TO authenticated
    USING (member_id = auth.uid() OR public.is_admin());

-- Members can insert their own registration
CREATE POLICY "Members can register for events"
    ON public.registrations FOR INSERT
    TO authenticated
    WITH CHECK (member_id = auth.uid());

-- Only admins can update registration status (e.g. approve, reject, mark attended)
CREATE POLICY "Admins can update registrations"
    ON public.registrations FOR UPDATE
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- Members can cancel their own registration
CREATE POLICY "Members can delete their own registration"
    ON public.registrations FOR DELETE
    TO authenticated
    USING (member_id = auth.uid() OR public.is_admin());

-- --- HACKATHON REGISTRATIONS POLICIES ---
CREATE POLICY "Members view own hackathon registrations, admins view all"
    ON public.hackathon_registrations FOR SELECT
    TO authenticated
    USING (member_id = auth.uid() OR public.is_admin());

CREATE POLICY "Members can register for hackathons"
    ON public.hackathon_registrations FOR INSERT
    TO authenticated
    WITH CHECK (member_id = auth.uid());

CREATE POLICY "Admins can update hackathon registrations"
    ON public.hackathon_registrations FOR UPDATE
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- --- LEADERBOARD POLICIES ---
-- All authenticated users can read the leaderboard
CREATE POLICY "Leaderboard viewable by authenticated users"
    ON public.leaderboard FOR SELECT
    TO authenticated
    USING (true);

-- Only admins can award or modify points
CREATE POLICY "Only admins can award leaderboard points"
    ON public.leaderboard FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- ==============================================================================
-- STORAGE BUCKETS SETUP (Supabase Storage)
-- Run these via Supabase SQL Editor to initialize storage
-- ==============================================================================
INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('posters', 'posters', true),
    ('avatars', 'avatars', true),
    ('event-photos', 'event-photos', true)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS: Public read access for images & posters
CREATE POLICY "Public can view posters and photos"
    ON storage.objects FOR SELECT
    TO public
    USING (bucket_id IN ('posters', 'avatars', 'event-photos'));

-- Storage RLS: Authenticated users can upload avatars
CREATE POLICY "Authenticated users can upload avatars"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id = 'avatars');

-- Storage RLS: Only admins can upload to posters and event-photos
CREATE POLICY "Admins can upload posters and photos"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id IN ('posters', 'event-photos') AND public.is_admin());

-- ==============================================================================
-- INSTRUCTIONS TO CREATE FIRST ADMIN ACCOUNT
-- ==============================================================================
-- 1. Sign up a new user via the website register page (or Supabase Auth Dashboard).
--    e.g., email: 'admin@analytixclub.edu'
-- 2. Open your Supabase Dashboard -> SQL Editor, and run:
--
--    UPDATE public.profiles 
--    SET role = 'admin', team = 'Tech' 
--    WHERE email = 'admin@analytixclub.edu';
--
-- 3. That user will immediately have full admin rights across the website and APIs!
-- 4. That admin can now promote other admins directly through the Admin Dashboard UI.
-- ==============================================================================

