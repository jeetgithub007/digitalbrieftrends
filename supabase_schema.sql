-- ============================================================================
-- DIGITALBRIEF SUPABASE DATABASE MIGRATION SCRIPT
-- Copy and paste this script into your Supabase SQL Editor (Database -> SQL Editor)
-- ============================================================================

-- 1. PROFILES TABLE (Linked to Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'free' CHECK (role IN ('free', 'subscriber', 'admin')),
    subscription_status TEXT NOT NULL DEFAULT 'inactive' CHECK (subscription_status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. AUTOMATIC USER PROFILE TRIGGER
-- Auto-creates user profile on signup.
-- Special Rule: If email = 'j.parganiha@gmail.com', auto-assign role = 'admin' and subscription_status = 'active'!
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, role, subscription_status)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', SPLIT_PART(NEW.email, '@', 1)),
        CASE 
            WHEN LOWER(NEW.email) = 'j.parganiha@gmail.com' THEN 'admin'
            ELSE 'free'
        END,
        CASE 
            WHEN LOWER(NEW.email) = 'j.parganiha@gmail.com' THEN 'active'
            ELSE 'inactive'
        END
    )
    ON CONFLICT (id) DO UPDATE SET
        role = EXCLUDED.role,
        subscription_status = EXCLUDED.subscription_status,
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Re-create Trigger on auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 3. ARTICLES TABLE (30-Day Automated Retention Lifecycle)
CREATE TABLE IF NOT EXISTS public.articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content TEXT,
    excerpt TEXT,
    category TEXT NOT NULL DEFAULT 'Technology',
    tags TEXT[],
    featured_image TEXT,
    image_alt TEXT,
    author TEXT DEFAULT 'DigitalBrief Editorial Desk',
    source TEXT,
    source_url TEXT,
    original_news_id TEXT,
    status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('published', 'draft', 'archived')),
    published_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    seo_title TEXT,
    meta_description TEXT,
    focus_keyword TEXT,
    secondary_keywords TEXT[],
    faq JSONB DEFAULT '[]'::jsonb
);

-- 4. AUTOMATIC UPDATE TIMESTAMP TRIGGER FOR ARTICLES
-- Resets the 30-day retention timer whenever an article is updated by Admin.
CREATE OR REPLACE FUNCTION public.update_article_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_article_timestamp ON public.articles;
CREATE TRIGGER trigger_update_article_timestamp
    BEFORE UPDATE ON public.articles
    FOR EACH ROW EXECUTE FUNCTION public.update_article_timestamp();

-- 5. AUTOMATED 30-DAY ARTICLE DELETION FUNCTION
-- Deletes articles where updated_at (or created_at) is older than 30 days.
CREATE OR REPLACE FUNCTION public.delete_expired_articles()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.articles
    WHERE COALESCE(updated_at, published_at, created_at) < (NOW() - INTERVAL '30 days');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 6. ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;

-- Profiles RLS Policies
DROP POLICY IF EXISTS "Public profiles are viewable by owner and admin" ON public.profiles;
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (
        auth.uid() = id OR 
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

DROP POLICY IF EXISTS "Users can update own profile or admin can update all" ON public.profiles;
CREATE POLICY "Users can update own profile or admin can update all" ON public.profiles
    FOR UPDATE USING (
        auth.uid() = id OR 
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- Articles RLS Policies
DROP POLICY IF EXISTS "Published articles are viewable by everyone" ON public.articles;
CREATE POLICY "Published articles are viewable by everyone" ON public.articles
    FOR SELECT USING (status = 'published' OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'));

DROP POLICY IF EXISTS "Only admins can insert or update articles" ON public.articles;
CREATE POLICY "Only admins can insert or update articles" ON public.articles
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- 7. SEED INITIAL ADMIN USER PROFILE (For j.parganiha@gmail.com if user exists)
DO $$
BEGIN
    UPDATE public.profiles
    SET role = 'admin', subscription_status = 'active'
    WHERE LOWER(email) = 'j.parganiha@gmail.com';
END $$;
