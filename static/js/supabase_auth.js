// ============================================================================
// DIGITALBRIEF SUPABASE AUTHENTICATION & ROLE-BASED ACCESS CONTROL ENGINE
// ============================================================================
const SUPABASE_URL = "https://wlfxoemctfxnoahyardf.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndsZnhvZW1jdGZ4bm9haHlhcmRmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA4MzU5MjcsImV4cCI6MjEwNjQxMTkyN30.HThihr1fP264vZqYwwbkQlvLOVGibWfD5yv3DUg5_8k";

let supabaseClient = null;
let currentUser = null;
let currentUserProfile = null;

function getSupabaseClient() {
    if (!supabaseClient && window.supabase) {
        try {
            supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        } catch (e) {
            console.error("Supabase client init error:", e);
        }
    }
    return supabaseClient;
}

// Global Auth Initialization
async function initDigitalBriefAuth() {
    let client = getSupabaseClient();
    if (!client) {
        for (let i = 0; i < 5; i++) {
            await new Promise(r => setTimeout(r, 200));
            client = getSupabaseClient();
            if (client) break;
        }
    }
    
    if (!client) {
        console.warn("Supabase SDK not loaded yet.");
        updateAuthUI();
        return;
    }

    try {
        const { data: { session } } = await client.auth.getSession();
        if (session && session.user) {
            currentUser = session.user;
            await fetchUserProfile(currentUser.id);
        }
    } catch (e) {
        console.error("Auth init error:", e);
    }

    client.auth.onAuthStateChange(async (event, session) => {
        if (session && session.user) {
            currentUser = session.user;
            await fetchUserProfile(currentUser.id);
        } else {
            currentUser = null;
            currentUserProfile = null;
        }
        updateAuthUI();
    });

    updateAuthUI();
}

async function fetchUserProfile(userId) {
    const client = getSupabaseClient();
    if (!client) return;

    try {
        const { data, error } = await client
            .from('profiles')
            .select('*')
            .eq('id', userId)
            .single();
            
        if (data) {
            currentUserProfile = data;
        } else {
            const isAdmin = currentUser && currentUser.email.toLowerCase() === 'j.parganiha@gmail.com';
            currentUserProfile = {
                role: isAdmin ? 'admin' : 'free',
                subscription_status: isAdmin ? 'active' : 'inactive'
            };
        }
    } catch (e) {
        const isAdmin = currentUser && currentUser.email.toLowerCase() === 'j.parganiha@gmail.com';
        currentUserProfile = {
            role: isAdmin ? 'admin' : 'free',
            subscription_status: isAdmin ? 'active' : 'inactive'
        };
    }
}

function updateAuthUI() {
    const authContainer = document.getElementById('userAuthContainer');
    if (!authContainer) return;

    if (currentUser) {
        const email = currentUser.email;
        const isAdmin = email.toLowerCase() === 'j.parganiha@gmail.com' || (currentUserProfile && currentUserProfile.role === 'admin');
        const isSubscriber = (currentUserProfile && currentUserProfile.subscription_status === 'active') || isAdmin;
        
        const badgeColor = isAdmin ? '#a855f7' : (isSubscriber ? '#10b981' : '#94a3b8');
        const badgeText = isAdmin ? '👑 Super Admin' : (isSubscriber ? '⚡ Pro Subscriber' : '👤 Free User');

        authContainer.innerHTML = `
            <div style="display:inline-flex; align-items:center; gap:8px;">
                <span style="font-size:0.75rem; background:rgba(255,255,255,0.06); border:1px solid ${badgeColor}; color:${badgeColor}; padding:4px 9px; border-radius:6px; font-weight:700;">
                    ${badgeText}
                </span>
                ${isAdmin ? '<a href="/admin" class="btn-btn btn-primary" style="padding:6px 12px; font-size:0.78rem;">⚙️ Admin CMS</a>' : ''}
                <button type="button" onclick="handleSignOut()" class="btn-btn btn-outline" style="padding:6px 12px; font-size:0.78rem;">Logout</button>
            </div>
        `;
    } else {
        authContainer.innerHTML = `
            <div style="display:inline-flex; gap:6px;">
                <button type="button" onclick="openAuthModal('login')" class="btn-btn btn-primary" style="padding:6px 12px; font-size:0.8rem; cursor:pointer;">🔑 User Login</button>
                <button type="button" onclick="openAuthModal('admin')" class="btn-btn btn-outline" style="padding:6px 12px; font-size:0.8rem; cursor:pointer; border-color:#a855f7; color:#a855f7;">👑 Admin Login</button>
            </div>
        `;
    }
}

async function handleSignOut() {
    const client = getSupabaseClient();
    if (client) {
        await client.auth.signOut();
        currentUser = null;
        currentUserProfile = null;
        window.location.reload();
    }
}

function isAdminUser() {
    if (!currentUser) return false;
    return currentUser.email.toLowerCase() === 'j.parganiha@gmail.com' || (currentUserProfile && currentUserProfile.role === 'admin');
}

// Feature Access Verification for Dashboard Interactive Features
function checkSubscriberAccess(featureName) {
    if (currentUser) {
        const isAdmin = isAdminUser();
        const isSubscriber = (currentUserProfile && currentUserProfile.subscription_status === 'active') || isAdmin;
        if (isSubscriber) return true;
    }

    showSubscriberUpgradeModal(featureName);
    return false;
}

// Display High-Tech Pro Subscriber Upgrade Modal
function showSubscriberUpgradeModal(featureName) {
    let modal = document.getElementById('subscriberUpgradeModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'subscriberUpgradeModal';
        modal.style.cssText = 'position:fixed; inset:0; z-index:999999; background:rgba(5,8,17,0.85); backdrop-filter:blur(12px); display:flex; align-items:center; justify-content:center; padding:20px;';
        document.body.appendChild(modal);
    }

    const featureTitle = featureName || 'Interactive Feature';
    const userEmailText = currentUser ? `Logged in as: <strong>${currentUser.email}</strong> (Free Tier)` : 'You are currently browsing as a Guest';

    modal.innerHTML = `
        <div style="background:#0e131f; border:1px solid #6366f1; border-radius:18px; max-width:480px; width:100%; padding:32px; box-shadow:0 20px 50px rgba(0,0,0,0.8); text-align:center; position:relative; font-family:'Plus Jakarta Sans', system-ui, sans-serif;">
            <button type="button" onclick="closeSubscriberModal()" style="position:absolute; top:16px; right:16px; background:none; border:none; color:#94a3b8; font-size:1.4rem; cursor:pointer;">✕</button>
            <div style="width:54px; height:54px; background:rgba(99,102,241,0.15); border:1px solid #6366f1; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:1.6rem; margin:0 auto 16px auto; color:#818cf8;">🔒</div>
            <h3 style="font-size:1.4rem; font-weight:800; color:#fff; margin-bottom:10px;">Pro Subscriber Feature Restricted</h3>
            <p style="color:#cbd5e1; font-size:0.92rem; line-height:1.55; margin-bottom:20px;">
                Access to <strong>${featureTitle}</strong> (including real-time analytics, dataset export, live crawler execution, category filtering, and story bookmarking) is reserved exclusively for <strong>DigitalBrief Pro Subscribers</strong>.
            </p>
            <div style="font-size:0.8rem; color:#94a3b8; margin-bottom:24px; padding:10px; background:rgba(255,255,255,0.04); border-radius:8px;">
                ${userEmailText}
            </div>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <button type="button" onclick="closeSubscriberModal(); openAuthModal('login');" style="background:linear-gradient(135deg,#6366f1,#4f46e5); color:#fff; border:none; padding:12px; border-radius:10px; font-weight:800; font-size:0.92rem; cursor:pointer;">
                    ${currentUser ? '⚡ Upgrade to Pro Subscription' : '🔑 Log In / Register Account'}
                </button>
                <button type="button" onclick="closeSubscriberModal()" style="background:rgba(255,255,255,0.06); color:#cbd5e1; border:1px solid #1e293b; padding:10px; border-radius:10px; font-weight:600; font-size:0.85rem; cursor:pointer;">
                    Continue Reading News Preview
                </button>
            </div>
        </div>
    `;
    modal.style.display = 'flex';
}

function closeSubscriberModal() {
    const modal = document.getElementById('subscriberUpgradeModal');
    if (modal) modal.style.display = 'none';
}

let authMode = 'login';

// Dedicated User & Super Admin Login Modal
function openAuthModal(defaultTab = 'login') {
    let modal = document.getElementById('digitalBriefAuthModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'digitalBriefAuthModal';
        modal.style.cssText = 'position:fixed; inset:0; z-index:999999; background:rgba(5,8,17,0.85); backdrop-filter:blur(12px); display:flex; align-items:center; justify-content:center; padding:20px;';
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
        <div style="background:#0e131f; border:1px solid #1e293b; border-radius:20px; max-width:440px; width:100%; padding:32px; box-shadow:0 25px 60px rgba(0,0,0,0.9); position:relative; font-family:'Plus Jakarta Sans', system-ui, sans-serif;">
            <button type="button" onclick="closeAuthModal()" style="position:absolute; top:16px; right:16px; background:none; border:none; color:#94a3b8; font-size:1.4rem; cursor:pointer; padding:4px 8px;">✕</button>
            
            <div style="display:flex; gap:8px; margin-bottom:20px; border-bottom:1px solid #1e293b; padding-bottom:12px;">
                <button type="button" id="tabUserBtn" onclick="switchAuthTab('login')" style="flex:1; background:none; border:none; color:#fff; font-weight:700; font-size:0.88rem; cursor:pointer; border-bottom:2px solid #6366f1; padding-bottom:8px; transition:all 0.2s;">
                    👤 User Login
                </button>
                <button type="button" id="tabAdminBtn" onclick="switchAuthTab('admin')" style="flex:1; background:none; border:none; color:#64748b; font-weight:700; font-size:0.88rem; cursor:pointer; padding-bottom:8px; transition:all 0.2s;">
                    👑 Super Admin
                </button>
                <button type="button" id="tabRegisterBtn" onclick="switchAuthTab('register')" style="flex:1; background:none; border:none; color:#64748b; font-weight:700; font-size:0.88rem; cursor:pointer; padding-bottom:8px; transition:all 0.2s;">
                    ✨ Register
                </button>
            </div>

            <div id="authAlert" style="display:none; padding:12px 14px; border-radius:10px; font-size:0.85rem; margin-bottom:16px; line-height:1.4;"></div>

            <form id="authForm" onsubmit="handleAuthSubmit(event)">
                <div id="nameGroup" style="display:none; margin-bottom:14px;">
                    <label style="display:block; font-size:0.8rem; font-weight:700; color:#cbd5e1; margin-bottom:6px;">Full Name</label>
                    <input type="text" id="authName" placeholder="Enter your full name" style="width:100%; padding:11px 14px; border-radius:10px; border:1px solid #1e293b; background:#050811; color:#fff; font-size:0.9rem; outline:none;">
                </div>

                <div style="margin-bottom:14px;">
                    <label id="authEmailLabel" style="display:block; font-size:0.8rem; font-weight:700; color:#cbd5e1; margin-bottom:6px;">Email Address</label>
                    <input type="email" id="authEmail" placeholder="name@domain.com" required style="width:100%; padding:11px 14px; border-radius:10px; border:1px solid #1e293b; background:#050811; color:#fff; font-size:0.9rem; outline:none;">
                </div>

                <div style="margin-bottom:20px;">
                    <label style="display:block; font-size:0.8rem; font-weight:700; color:#cbd5e1; margin-bottom:6px;">Password</label>
                    <input type="password" id="authPassword" placeholder="••••••••" required style="width:100%; padding:11px 14px; border-radius:10px; border:1px solid #1e293b; background:#050811; color:#fff; font-size:0.9rem; outline:none;">
                </div>

                <button type="submit" id="authSubmitBtn" style="width:100%; background:linear-gradient(135deg,#6366f1,#4f46e5); color:#fff; border:none; padding:12px; border-radius:10px; font-weight:800; font-size:0.92rem; cursor:pointer; box-shadow:0 4px 14px rgba(99,102,241,0.4);">
                    Sign In to DigitalBrief
                </button>
            </form>

            <div id="authNotice" style="margin-top:16px; font-size:0.78rem; color:#64748b; text-align:center;">
                Access news, trending keywords & subscriber tools
            </div>
        </div>
    `;
    modal.style.display = 'flex';
    switchAuthTab(defaultTab);
}

function closeAuthModal() {
    const modal = document.getElementById('digitalBriefAuthModal');
    if (modal) modal.style.display = 'none';
}

function switchAuthTab(mode) {
    authMode = mode;
    const userBtn = document.getElementById('tabUserBtn');
    const adminBtn = document.getElementById('tabAdminBtn');
    const regBtn = document.getElementById('tabRegisterBtn');
    const nameGroup = document.getElementById('nameGroup');
    const emailInput = document.getElementById('authEmail');
    const submitBtn = document.getElementById('authSubmitBtn');
    const noticeEl = document.getElementById('authNotice');

    [userBtn, adminBtn, regBtn].forEach(b => {
        if (b) { b.style.color = '#64748b'; b.style.borderBottom = 'none'; }
    });

    if (mode === 'login') {
        if (userBtn) { userBtn.style.color = '#fff'; userBtn.style.borderBottom = '2px solid #6366f1'; }
        if (nameGroup) nameGroup.style.display = 'none';
        if (submitBtn) { submitBtn.innerText = '⚡ Sign In to User Dashboard'; submitBtn.style.background = 'linear-gradient(135deg,#6366f1,#4f46e5)'; }
        if (noticeEl) noticeEl.innerHTML = 'Sign in to access your subscriber dashboard & features';
    } else if (mode === 'admin') {
        if (adminBtn) { adminBtn.style.color = '#a855f7'; adminBtn.style.borderBottom = '2px solid #a855f7'; }
        if (nameGroup) nameGroup.style.display = 'none';
        if (emailInput && !emailInput.value) emailInput.value = 'j.parganiha@gmail.com';
        if (submitBtn) { submitBtn.innerText = '👑 Authenticate & Launch Admin CMS'; submitBtn.style.background = 'linear-gradient(135deg,#a855f7,#9333ea)'; }
        if (noticeEl) noticeEl.innerHTML = '<strong>Super Admin Access:</strong> Restricted to <code>j.parganiha@gmail.com</code>';
    } else {
        if (regBtn) { regBtn.style.color = '#10b981'; regBtn.style.borderBottom = '2px solid #10b981'; }
        if (nameGroup) nameGroup.style.display = 'block';
        if (submitBtn) { submitBtn.innerText = '🚀 Create Account'; submitBtn.style.background = 'linear-gradient(135deg,#10b981,#059669)'; }
        if (noticeEl) noticeEl.innerHTML = 'Join DigitalBrief to unlock subscriber intelligence & alerts';
    }
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const client = getSupabaseClient();
    const alertBox = document.getElementById('authAlert');
    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value;
    const name = document.getElementById('authName') ? document.getElementById('authName').value.trim() : '';

    if (!client) {
        alertBox.style.display = 'block';
        alertBox.style.background = 'rgba(239,68,68,0.2)';
        alertBox.style.color = '#f87171';
        alertBox.innerText = 'Supabase client unavailable. Please refresh page.';
        return;
    }

    alertBox.style.display = 'block';
    alertBox.style.background = 'rgba(99,102,241,0.2)';
    alertBox.style.color = '#818cf8';
    alertBox.innerText = 'Authenticating with Supabase...';

    try {
        if (authMode === 'login' || authMode === 'admin') {
            const { data, error } = await client.auth.signInWithPassword({ email, password });
            if (error) throw error;
            
            const isAdmin = email.toLowerCase() === 'j.parganiha@gmail.com';
            alertBox.style.background = 'rgba(16,185,129,0.2)';
            alertBox.style.color = '#34d399';
            alertBox.innerText = isAdmin ? '👑 Super Admin Authenticated! Launching CMS...' : 'Success! Logging in...';
            
            setTimeout(() => {
                closeAuthModal();
                if (isAdmin || authMode === 'admin') {
                    window.location.href = '/admin';
                } else {
                    window.location.reload();
                }
            }, 600);
        } else {
            const { data, error } = await client.auth.signUp({
                email,
                password,
                options: { data: { full_name: name } }
            });
            if (error) throw error;
            alertBox.style.background = 'rgba(16,185,129,0.2)';
            alertBox.style.color = '#34d399';
            alertBox.innerText = 'Account created successfully! Logging in...';
            setTimeout(() => { closeAuthModal(); window.location.reload(); }, 800);
        }
    } catch (err) {
        alertBox.style.background = 'rgba(239,68,68,0.2)';
        alertBox.style.color = '#f87171';
        alertBox.innerText = err.message || 'Authentication failed. Please check credentials.';
    }
}

// Bind functions globally
window.openAuthModal = openAuthModal;
window.closeAuthModal = closeAuthModal;
window.switchAuthTab = switchAuthTab;
window.handleAuthSubmit = handleAuthSubmit;
window.handleSignOut = handleSignOut;
window.showSubscriberUpgradeModal = showSubscriberUpgradeModal;
window.closeSubscriberModal = closeSubscriberModal;
window.checkSubscriberAccess = checkSubscriberAccess;
window.isAdminUser = isAdminUser;
window.initDigitalBriefAuth = initDigitalBriefAuth;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDigitalBriefAuth);
} else {
    initDigitalBriefAuth();
}
