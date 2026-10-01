// ============================================================================
// DIGITALBRIEF SUPABASE AUTHENTICATION & ROLE-BASED ACCESS CONTROL ENGINE
// ============================================================================
const SUPABASE_URL = "https://wlfxoemctfxnoahyardf.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndsZnhvZW1jdGZ4bm9haHlhcmRmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA4MzU5MjcsImV4cCI6MjEwNjQxMTkyN30.HThihr1fP264vZqYwwbkQlvLOVGibWfD5yv3DUg5_8k";

let supabaseClient = null;
let currentUser = null;
let currentUserProfile = null;

if (window.supabase) {
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

// Global Auth Initialization
async function initDigitalBriefAuth() {
    if (!supabaseClient) return;

    try {
        const { data: { session } } = await supabaseClient.auth.getSession();
        if (session && session.user) {
            currentUser = session.user;
            await fetchUserProfile(currentUser.id);
        }
    } catch (e) {
        console.error("Auth init error:", e);
    }

    // Subscribe to auth state changes
    supabaseClient.auth.onAuthStateChange(async (event, session) => {
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
    try {
        const { data, error } = await supabaseClient
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
        const badgeText = isAdmin ? '👑 Admin' : (isSubscriber ? '⚡ Pro Subscriber' : '👤 Free Tier');

        authContainer.innerHTML = `
            <div style="display:inline-flex; align-items:center; gap:8px;">
                <span style="font-size:0.75rem; background:rgba(255,255,255,0.06); border:1px solid ${badgeColor}; color:${badgeColor}; padding:4px 9px; border-radius:6px; font-weight:700;">
                    ${badgeText}
                </span>
                ${isAdmin ? '<a href="/admin" class="btn-btn btn-primary" style="padding:6px 12px; font-size:0.78rem;">⚙️ Admin</a>' : ''}
                <button onclick="handleSignOut()" class="btn-btn btn-outline" style="padding:6px 12px; font-size:0.78rem;">Logout</button>
            </div>
        `;
    } else {
        authContainer.innerHTML = `
            <button onclick="openAuthModal()" class="btn-btn btn-primary" style="padding:6px 14px; font-size:0.8rem;">🔐 Login / Register</button>
        `;
    }
}

async function handleSignOut() {
    if (supabaseClient) {
        await supabaseClient.auth.signOut();
        currentUser = null;
        currentUserProfile = null;
        window.location.reload();
    }
}

function isAdminUser() {
    if (!currentUser) return false;
    return currentUser.email.toLowerCase() === 'j.parganiha@gmail.com' || (currentUserProfile && currentUserProfile.role === 'admin');
}
window.isAdminUser = isAdminUser;

// Feature Access Verification for Dashboard Interactive Features
function checkSubscriberAccess(featureName) {
    // Admin (j.parganiha@gmail.com) or active Pro Subscriber has full access
    if (currentUser) {
        const isAdmin = isAdminUser();
        const isSubscriber = (currentUserProfile && currentUserProfile.subscription_status === 'active') || isAdmin;
        if (isSubscriber) return true;
    }

    // Otherwise block feature access and display upgrade modal
    showSubscriberUpgradeModal(featureName);
    return false;
}

// Display High-Tech Pro Subscriber Upgrade Modal
function showSubscriberUpgradeModal(featureName) {
    let modal = document.getElementById('subscriberUpgradeModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'subscriberUpgradeModal';
        modal.style.cssText = 'position:fixed; inset:0; z-index:9999; background:rgba(5,8,17,0.85); backdrop-filter:blur(12px); display:flex; align-items:center; justify-content:center; padding:20px;';
        document.body.appendChild(modal);
    }

    const featureTitle = featureName || 'Interactive Feature';
    const userEmailText = currentUser ? `Logged in as: <strong>${currentUser.email}</strong> (Free Tier)` : 'You are currently browsing as a Guest';

    modal.innerHTML = `
        <div style="background:#0e131f; border:1px solid #6366f1; border-radius:18px; max-width:480px; width:100%; padding:32px; box-shadow:0 20px 50px rgba(0,0,0,0.8); text-align:center; position:relative;">
            <button onclick="closeSubscriberModal()" style="position:absolute; top:16px; right:16px; background:none; border:none; color:#94a3b8; font-size:1.2rem; cursor:pointer;">✕</button>
            <div style="width:54px; height:54px; background:rgba(99,102,241,0.15); border:1px solid #6366f1; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:1.6rem; margin:0 auto 16px auto; color:#818cf8;">🔒</div>
            <h3 style="font-size:1.4rem; font-weight:800; color:#fff; margin-bottom:10px;">Pro Subscriber Feature Restricted</h3>
            <p style="color:#cbd5e1; font-size:0.92rem; line-height:1.55; margin-bottom:20px;">
                Access to <strong>${featureTitle}</strong> (including real-time analytics, dataset export, live crawler execution, category filtering, and story bookmarking) is reserved exclusively for <strong>DigitalBrief Pro Subscribers</strong>.
            </p>
            <div style="font-size:0.8rem; color:#94a3b8; margin-bottom:24px; padding:10px; background:rgba(255,255,255,0.04); border-radius:8px;">
                ${userEmailText}
            </div>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <button onclick="closeSubscriberModal(); openAuthModal();" style="background:linear-gradient(135deg,#6366f1,#4f46e5); color:#fff; border:none; padding:12px; border-radius:10px; font-weight:800; font-size:0.92rem; cursor:pointer;">
                    ${currentUser ? '⚡ Upgrade to Pro Subscription' : '🔑 Log In / Register Account'}
                </button>
                <button onclick="closeSubscriberModal()" style="background:rgba(255,255,255,0.06); color:#cbd5e1; border:1px solid #1e293b; padding:10px; border-radius:10px; font-weight:600; font-size:0.85rem; cursor:pointer;">
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

// User Auth Modal (Sign In / Register)
function openAuthModal() {
    let modal = document.getElementById('digitalBriefAuthModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'digitalBriefAuthModal';
        modal.style.cssText = 'position:fixed; inset:0; z-index:9999; background:rgba(5,8,17,0.85); backdrop-filter:blur(12px); display:flex; align-items:center; justify-content:center; padding:20px;';
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
        <div style="background:#0e131f; border:1px solid #1e293b; border-radius:18px; max-width:420px; width:100%; padding:30px; box-shadow:0 20px 50px rgba(0,0,0,0.8); position:relative;">
            <button onclick="closeAuthModal()" style="position:absolute; top:16px; right:16px; background:none; border:none; color:#94a3b8; font-size:1.2rem; cursor:pointer;">✕</button>
            
            <div style="display:flex; gap:10px; margin-bottom:20px; border-bottom:1px solid #1e293b; padding-bottom:10px;">
                <button id="tabLoginBtn" onclick="switchAuthTab('login')" style="background:none; border:none; color:#fff; font-weight:800; font-size:1.05rem; cursor:pointer; border-bottom:2px solid #6366f1; padding-bottom:4px;">Sign In</button>
                <button id="tabRegisterBtn" onclick="switchAuthTab('register')" style="background:none; border:none; color:#64748b; font-weight:700; font-size:1.05rem; cursor:pointer; padding-bottom:4px;">Create Account</button>
            </div>

            <div id="authAlert" style="display:none; padding:10px; border-radius:8px; font-size:0.84rem; margin-bottom:14px;"></div>

            <form id="authForm" onsubmit="handleAuthSubmit(event)">
                <div id="nameGroup" style="display:none; margin-bottom:14px;">
                    <label style="display:block; font-size:0.8rem; font-weight:700; color:#cbd5e1; margin-bottom:6px;">Full Name</label>
                    <input type="text" id="authName" placeholder="Enter your name" style="width:100%; padding:10px 14px; border-radius:8px; border:1px solid #1e293b; background:#050811; color:#fff; font-size:0.9rem;">
                </div>

                <div style="margin-bottom:14px;">
                    <label style="display:block; font-size:0.8rem; font-weight:700; color:#cbd5e1; margin-bottom:6px;">Email Address</label>
                    <input type="email" id="authEmail" placeholder="name@domain.com" required style="width:100%; padding:10px 14px; border-radius:8px; border:1px solid #1e293b; background:#050811; color:#fff; font-size:0.9rem;">
                </div>

                <div style="margin-bottom:20px;">
                    <label style="display:block; font-size:0.8rem; font-weight:700; color:#cbd5e1; margin-bottom:6px;">Password</label>
                    <input type="password" id="authPassword" placeholder="••••••••" required style="width:100%; padding:10px 14px; border-radius:8px; border:1px solid #1e293b; background:#050811; color:#fff; font-size:0.9rem;">
                </div>

                <button type="submit" id="authSubmitBtn" style="width:100%; background:linear-gradient(135deg,#6366f1,#4f46e5); color:#fff; border:none; padding:12px; border-radius:10px; font-weight:800; font-size:0.92rem; cursor:pointer;">
                    Sign In to DigitalBrief
                </button>
            </form>
        </div>
    `;
    modal.style.display = 'flex';
}

function closeAuthModal() {
    const modal = document.getElementById('digitalBriefAuthModal');
    if (modal) modal.style.display = 'none';
}

let authMode = 'login';
function switchAuthTab(mode) {
    authMode = mode;
    const loginBtn = document.getElementById('tabLoginBtn');
    const regBtn = document.getElementById('tabRegisterBtn');
    const nameGroup = document.getElementById('nameGroup');
    const submitBtn = document.getElementById('authSubmitBtn');

    if (mode === 'login') {
        loginBtn.style.color = '#fff'; loginBtn.style.borderBottom = '2px solid #6366f1';
        regBtn.style.color = '#64748b'; regBtn.style.borderBottom = 'none';
        nameGroup.style.display = 'none';
        submitBtn.innerText = 'Sign In to DigitalBrief';
    } else {
        regBtn.style.color = '#fff'; regBtn.style.borderBottom = '2px solid #6366f1';
        loginBtn.style.color = '#64748b'; loginBtn.style.borderBottom = 'none';
        nameGroup.style.display = 'block';
        submitBtn.innerText = 'Create Account';
    }
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const alertBox = document.getElementById('authAlert');
    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value;
    const name = document.getElementById('authName') ? document.getElementById('authName').value.trim() : '';

    alertBox.style.display = 'block';
    alertBox.style.background = 'rgba(99,102,241,0.2)';
    alertBox.style.color = '#818cf8';
    alertBox.innerText = 'Authenticating with Supabase...';

    try {
        if (authMode === 'login') {
            const { data, error } = await supabaseClient.auth.signInWithPassword({ email, password });
            if (error) throw error;
            alertBox.style.background = 'rgba(16,185,129,0.2)'; alertBox.style.color = '#34d399';
            alertBox.innerText = 'Success! Logging in...';
            setTimeout(() => { closeAuthModal(); window.location.reload(); }, 600);
        } else {
            const { data, error } = await supabaseClient.auth.signUp({
                email,
                password,
                options: { data: { full_name: name } }
            });
            if (error) throw error;
            alertBox.style.background = 'rgba(16,185,129,0.2)'; alertBox.style.color = '#34d399';
            alertBox.innerText = 'Account created successfully! Logging in...';
            setTimeout(() => { closeAuthModal(); window.location.reload(); }, 800);
        }
    } catch (err) {
        alertBox.style.background = 'rgba(239,68,68,0.2)';
        alertBox.style.color = '#f87171';
        alertBox.innerText = err.message || 'Authentication failed. Please check credentials.';
    }
}

document.addEventListener('DOMContentLoaded', initDigitalBriefAuth);
