// ============================================================================
// DIGITALBRIEF SUPABASE AUTHENTICATION & ROLE-BASED ACCESS CONTROL ENGINE
// High-Tech Magazine UI Edition
// ============================================================================
const SUPABASE_URL = window.SUPABASE_URL || "https://vehxbphzorgaomzrbizc.supabase.co";
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlaHhicGh6b3JnYW9tenJiaXpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEwMDc4NDEsImV4cCI6MjEwNjQxMTkyN30.mKeoUK24H__I0VVSsMDIQpq6WEYkiElRJdwzVJFxsqA";

let supabaseClient = null;
let currentUser = null;
let currentUserProfile = null;

// Inject High-Tech Auth Styles automatically
(function injectAuthStyles() {
    if (document.getElementById('digitalbrief-tech-auth-styles')) return;
    const style = document.createElement('style');
    style.id = 'digitalbrief-tech-auth-styles';
    style.textContent = `
        .tech-auth-btn-wrap { display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .tech-auth-btn {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 7px 15px; border-radius: 8px;
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
            font-size: 0.8rem; font-weight: 700; cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            outline: none; letter-spacing: 0.2px; text-decoration: none;
        }
        .tech-auth-btn-user {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.18), rgba(79, 70, 229, 0.28));
            border: 1px solid rgba(99, 102, 241, 0.5); color: #a5b4fc;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
        }
        .tech-auth-btn-user:hover {
            background: linear-gradient(135deg, #6366f1, #4f46e5);
            border-color: #818cf8; color: #ffffff;
            transform: translateY(-2px); box-shadow: 0 6px 18px rgba(99, 102, 241, 0.45);
        }
        .tech-auth-btn-admin {
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.18), rgba(147, 51, 234, 0.28));
            border: 1px solid rgba(168, 85, 247, 0.5); color: #c084fc;
            box-shadow: 0 4px 12px rgba(168, 85, 247, 0.15);
        }
        .tech-auth-btn-admin:hover {
            background: linear-gradient(135deg, #a855f7, #9333ea);
            border-color: #e879f9; color: #ffffff;
            transform: translateY(-2px); box-shadow: 0 6px 18px rgba(168, 85, 247, 0.45);
        }
        .tech-auth-badge {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 4px 10px; border-radius: 6px; font-size: 0.75rem;
            font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase;
        }
    `;
    document.head.appendChild(style);
})();

function getSupabaseClient() {
    if (!supabaseClient && window.supabase) {
        try {
            const url = window.SUPABASE_URL || SUPABASE_URL;
            const key = window.SUPABASE_ANON_KEY || SUPABASE_ANON_KEY;
            if (url && key && url.startsWith('http') && !url.includes('YOUR_NEW')) {
                supabaseClient = window.supabase.createClient(url, key);
            }
        } catch (e) {
            console.warn("Supabase client init pending new project credentials:", e);
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
        window.authReady = true;
        window.dispatchEvent(new CustomEvent('digitalbrief:authready'));
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
        window.authReady = true;
        window.dispatchEvent(new CustomEvent('digitalbrief:authready'));
    });

    updateAuthUI();
    window.authReady = true;
    window.dispatchEvent(new CustomEvent('digitalbrief:authready'));
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
        const isAdmin = isAdminUser();
        const isSubscriber = (currentUserProfile && currentUserProfile.subscription_status === 'active') || isAdmin;
        
        const badgeColor = isAdmin ? '#a855f7' : (isSubscriber ? '#10b981' : '#94a3b8');
        const badgeText = isAdmin ? '👑 Super Admin' : (isSubscriber ? '⚡ Pro Subscriber' : '👤 Free User');

        authContainer.innerHTML = `
            <div class="tech-auth-btn-wrap">
                <span class="tech-auth-badge" style="background:rgba(255,255,255,0.06); border:1px solid ${badgeColor}; color:${badgeColor};">
                    ${badgeText}
                </span>
                ${isAdmin ? '<a href="/admin" class="tech-auth-btn tech-auth-btn-admin">⚙️ Admin CMS</a>' : ''}
                <button type="button" onclick="handleSignOut()" class="tech-auth-btn tech-auth-btn-user" style="border-color:#334155; color:#cbd5e1;">Logout</button>
            </div>
        `;
    } else {
        authContainer.innerHTML = `
            <div class="tech-auth-btn-wrap">
                <button type="button" onclick="openAuthModal('login')" class="tech-auth-btn tech-auth-btn-user">🔑 User Login</button>
                <button type="button" onclick="openAuthModal('admin')" class="tech-auth-btn tech-auth-btn-admin">👑 Admin Login</button>
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
    if (currentUser && currentUser.email && currentUser.email.toLowerCase() === 'j.parganiha@gmail.com') {
        return true;
    }
    if (currentUserProfile && currentUserProfile.role === 'admin') {
        return true;
    }
    // Inspect local storage session as fallback
    try {
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.includes('sb-') || key.includes('supabase')) && key.includes('-auth-token')) {
                const sess = JSON.parse(localStorage.getItem(key));
                if (sess && sess.user && sess.user.email && sess.user.email.toLowerCase() === 'j.parganiha@gmail.com') {
                    return true;
                }
            }
        }
    } catch (e) {}
    return false;
}

// Feature Access Verification for Dashboard Interactive Features
function checkSubscriberAccess(featureName) {
    if (isAdminUser()) return true;
    if (currentUser) {
        const isSubscriber = (currentUserProfile && currentUserProfile.subscription_status === 'active');
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
        modal.style.cssText = 'position:fixed; inset:0; z-index:9999999; background:rgba(4,6,14,0.88); backdrop-filter:blur(16px); display:flex; align-items:center; justify-content:center; padding:20px;';
        document.body.appendChild(modal);
    }

    const featureTitle = featureName || 'Interactive Feature';
    const userEmailText = currentUser ? `Logged in as: <strong>${currentUser.email}</strong> (Free Tier)` : 'You are currently browsing as a Guest';

    modal.innerHTML = `
        <div style="background:#0e131f; border:1px solid #6366f1; border-radius:20px; max-width:480px; width:100%; padding:32px; box-shadow:0 25px 60px rgba(0,0,0,0.85); text-align:center; position:relative; font-family:'Plus Jakarta Sans', system-ui, sans-serif;">
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
                <button type="button" onclick="closeSubscriberModal(); openAuthModal('login');" class="tech-auth-btn tech-auth-btn-user" style="justify-content:center; padding:12px; font-size:0.92rem;">
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

// Display High-Tech Super Admin Only Modal
function showAdminOnlyModal(featureName) {
    let modal = document.getElementById('adminOnlyAccessModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'adminOnlyAccessModal';
        modal.style.cssText = 'position:fixed; inset:0; z-index:9999999; background:rgba(4,6,14,0.88); backdrop-filter:blur(16px); display:flex; align-items:center; justify-content:center; padding:20px;';
        document.body.appendChild(modal);
    }

    const featureTitle = featureName || 'Article Generation Engine';
    const userEmailText = currentUser ? `Logged in as: <strong>${currentUser.email}</strong>` : 'Currently browsing as Guest';

    modal.innerHTML = `
        <div style="background:#0e131f; border:1px solid #a855f7; border-radius:20px; max-width:460px; width:100%; padding:32px; box-shadow:0 25px 60px rgba(0,0,0,0.85); text-align:center; position:relative; font-family:'Plus Jakarta Sans', system-ui, sans-serif;">
            <button type="button" onclick="closeAdminOnlyModal()" style="position:absolute; top:16px; right:16px; background:none; border:none; color:#94a3b8; font-size:1.4rem; cursor:pointer;">✕</button>
            <div style="width:54px; height:54px; background:rgba(168,85,247,0.15); border:1px solid #a855f7; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:1.6rem; margin:0 auto 16px auto; color:#c084fc;">👑</div>
            <h3 style="font-size:1.35rem; font-weight:800; color:#fff; margin-bottom:10px;">Super Admin Authorization Required</h3>
            <p style="color:#cbd5e1; font-size:0.9rem; line-height:1.55; margin-bottom:20px;">
                <strong>${featureTitle}</strong> is restricted strictly to the <strong>Super Admin</strong> (<code>j.parganiha@gmail.com</code>). Regular subscribers and guest users cannot generate or publish articles.
            </p>
            <div style="font-size:0.8rem; color:#94a3b8; margin-bottom:24px; padding:10px; background:rgba(255,255,255,0.04); border-radius:8px;">
                ${userEmailText}
            </div>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <button type="button" onclick="closeAdminOnlyModal(); openAuthModal('admin');" class="tech-auth-btn tech-auth-btn-admin" style="justify-content:center; padding:12px; font-size:0.92rem;">
                    👑 Log In as Super Admin
                </button>
                <button type="button" onclick="closeAdminOnlyModal()" style="background:rgba(255,255,255,0.06); color:#cbd5e1; border:1px solid #1e293b; padding:10px; border-radius:10px; font-weight:600; font-size:0.85rem; cursor:pointer;">
                    Close Notification
                </button>
            </div>
        </div>
    `;
    modal.style.display = 'flex';
}

function closeAdminOnlyModal() {
    const modal = document.getElementById('adminOnlyAccessModal');
    if (modal) modal.style.display = 'none';
}

let authMode = 'login';

// Dedicated User & Super Admin Login Modal
function openAuthModal(defaultTab = 'login') {
    let modal = document.getElementById('digitalBriefAuthModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'digitalBriefAuthModal';
        modal.style.cssText = 'position:fixed; inset:0; z-index:9999999; background:rgba(4,6,14,0.88); backdrop-filter:blur(16px); display:flex; align-items:center; justify-content:center; padding:20px;';
        document.body.appendChild(modal);
    }

    // Force display FIRST
    modal.style.display = 'flex';

    modal.innerHTML = `
        <div style="background:#0e131f; border:1px solid #6366f1; border-radius:22px; max-width:440px; width:100%; padding:32px; box-shadow:0 25px 60px rgba(0,0,0,0.9); position:relative; font-family:'Plus Jakarta Sans', system-ui, sans-serif;">
            <button type="button" onclick="closeAuthModal()" style="position:absolute; top:16px; right:16px; background:none; border:none; color:#94a3b8; font-size:1.4rem; cursor:pointer; padding:4px 8px;">✕</button>
            
            <div style="display:flex; gap:6px; margin-bottom:20px; border-bottom:1px solid #1e293b; padding-bottom:12px;">
                <button type="button" id="tabUserBtn" onclick="switchAuthTab('login')" style="flex:1; background:none; border:none; color:#fff; font-weight:700; font-size:0.84rem; cursor:pointer; border-bottom:2px solid #6366f1; padding-bottom:8px; transition:all 0.2s;">
                    🔑 User Login
                </button>
                <button type="button" id="tabAdminBtn" onclick="switchAuthTab('admin')" style="flex:1; background:none; border:none; color:#64748b; font-weight:700; font-size:0.84rem; cursor:pointer; padding-bottom:8px; transition:all 0.2s;">
                    👑 Super Admin
                </button>
                <button type="button" id="tabRegisterBtn" onclick="switchAuthTab('register')" style="flex:1; background:none; border:none; color:#64748b; font-weight:700; font-size:0.84rem; cursor:pointer; padding-bottom:8px; transition:all 0.2s;">
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

                <button type="submit" id="authSubmitBtn" class="tech-auth-btn tech-auth-btn-user" style="width:100%; justify-content:center; padding:12px; font-size:0.92rem;">
                    Sign In to DigitalBrief
                </button>
            </form>

            <div id="authNotice" style="margin-top:16px; font-size:0.78rem; color:#64748b; text-align:center;">
                Access news, trending keywords & subscriber tools
            </div>
        </div>
    `;

    try {
        switchAuthTab(defaultTab);
    } catch (e) {
        console.error("switchAuthTab error:", e);
    }
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
        if (submitBtn) {
            submitBtn.innerText = '🔑 Sign In to User Dashboard';
            submitBtn.className = 'tech-auth-btn tech-auth-btn-user';
            submitBtn.style.cssText = 'width:100%; justify-content:center; padding:12px; font-size:0.92rem;';
        }
        if (noticeEl) noticeEl.innerHTML = 'Sign in to access your subscriber dashboard & features';
    } else if (mode === 'admin') {
        if (adminBtn) { adminBtn.style.color = '#c084fc'; adminBtn.style.borderBottom = '2px solid #a855f7'; }
        if (nameGroup) nameGroup.style.display = 'none';
        if (emailInput && !emailInput.value) emailInput.value = 'j.parganiha@gmail.com';
        if (submitBtn) {
            submitBtn.innerText = '👑 Authenticate & Launch Admin CMS';
            submitBtn.className = 'tech-auth-btn tech-auth-btn-admin';
            submitBtn.style.cssText = 'width:100%; justify-content:center; padding:12px; font-size:0.92rem;';
        }
        if (noticeEl) noticeEl.innerHTML = '<strong>Super Admin Access:</strong> Restricted to <code>j.parganiha@gmail.com</code>';
    } else {
        if (regBtn) { regBtn.style.color = '#34d399'; regBtn.style.borderBottom = '2px solid #10b981'; }
        if (nameGroup) nameGroup.style.display = 'block';
        if (submitBtn) {
            submitBtn.innerText = '🚀 Create User Account';
            submitBtn.className = 'tech-auth-btn';
            submitBtn.style.cssText = 'width:100%; justify-content:center; padding:12px; font-size:0.92rem; background:linear-gradient(135deg,#10b981,#059669); color:#fff; border:none;';
        }
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
            let res = await client.auth.signInWithPassword({ email, password });
            
            // Auto fallback to signUp if super admin doesn't exist in Supabase auth users yet
            if (res.error && email.toLowerCase() === 'j.parganiha@gmail.com') {
                res = await client.auth.signUp({
                    email,
                    password,
                    options: { data: { full_name: 'Super Admin' } }
                });
            }

            if (res.error) throw res.error;
            
            const isAdmin = email.toLowerCase() === 'j.parganiha@gmail.com';
            alertBox.style.background = 'rgba(16,185,129,0.2)';
            alertBox.style.color = '#34d399';
            alertBox.innerText = isAdmin ? '👑 Super Admin Authenticated! Launching CMS...' : 'Success! Logging in...';
            
            if (res.data && res.data.user) {
                currentUser = res.data.user;
            }

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
window.showAdminOnlyModal = showAdminOnlyModal;
window.closeAdminOnlyModal = closeAdminOnlyModal;
window.checkSubscriberAccess = checkSubscriberAccess;
window.isAdminUser = isAdminUser;
window.getSupabaseClient = getSupabaseClient;
window.initDigitalBriefAuth = initDigitalBriefAuth;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDigitalBriefAuth);
} else {
    initDigitalBriefAuth();
}
