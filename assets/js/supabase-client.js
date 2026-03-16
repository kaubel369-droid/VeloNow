/**
 * VeloNow Supabase Client & Auth Helper
 */

// Define the global object immediately to prevent "undefined" errors
window.velonowAuth = {
    supabase: null,
    isReady: false
};

(function() {
    console.log("VeloNow Auth: Script starting...");

    const SUPABASE_URL = 'https://cvqqrqdywzxeqqcetptz.supabase.co';
    const SUPABASE_ANON_KEY = 'sb_publishable_NJNcYL_hctQVm8Nzp5cG8g_XrJLwkCl';

    if (!window.supabase) {
        console.error("VeloNow Auth: Supabase library NOT found on window. Check script tags.");
        return;
    }

    try {
        const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        window.velonowAuth.supabase = client;
        console.log("VeloNow Auth: Supabase client initialized.");
    } catch (e) {
        console.error("VeloNow Auth: Failed to initialize Supabase client:", e);
        return;
    }

    async function getCurrentUser() {
        if (!window.velonowAuth.supabase) return null;
        try {
            const { data: { session }, error: sessionError } = await window.velonowAuth.supabase.auth.getSession();
            if (sessionError) throw sessionError;
            if (!session) return null;

            const { data: profile, error: profileError } = await window.velonowAuth.supabase
                .from('profiles')
                .select('*')
                .eq('id', session.user.id)
                .single();
            
            if (profileError) console.error("VeloNow Auth: Profile fetch error:", profileError);
            return { ...session.user, profile };
        } catch (err) {
            console.error("VeloNow Auth: getCurrentUser error:", err);
            return null;
        }
    }

    async function updateNav() {
        console.log("VeloNow Auth: Updating navigation...");
        const authNav = document.getElementById('auth-nav');
        if (!authNav) {
            console.log("VeloNow Auth: #auth-nav not found, skipping nav update.");
            return;
        }

        const user = await getCurrentUser();
        if (user) {
            authNav.innerHTML = `
                <a href="profile.html">Profile (${user.profile?.role || 'free'})</a>
                <a href="#" id="logout-btn" style="margin-left: 10px;">Logout</a>
            `;
            const logoutBtn = document.getElementById('logout-btn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    await window.velonowAuth.supabase.auth.signOut();
                    window.location.reload();
                });
            }
        } else {
            authNav.innerHTML = `<a href="auth.html">Login / Sign Up</a>`;
        }
    }

    // Assign methods to the global object
    window.velonowAuth.getCurrentUser = getCurrentUser;
    window.velonowAuth.updateNav = updateNav;
    window.velonowAuth.checkAccess = async function(requiredRoles) {
        const user = await getCurrentUser();
        const role = user?.profile?.role || 'free';
        return { hasAccess: requiredRoles.includes(role), user };
    };
    window.velonowAuth.protectContent = async function() {
        const premiumSections = document.querySelectorAll('.premium-content');
        const upgradeGate = document.getElementById('upgrade-gate');
        const { hasAccess } = await this.checkAccess(['subscriber', 'admin']);
        premiumSections.forEach(s => s.style.display = hasAccess ? 'block' : 'none');
        if (upgradeGate) upgradeGate.style.display = hasAccess ? 'none' : 'block';
    };

    window.velonowAuth.isReady = true;
    console.log("VeloNow Auth: Helper is ready.");

    // Auto-init
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateNav);
    } else {
        updateNav();
    }
})();
