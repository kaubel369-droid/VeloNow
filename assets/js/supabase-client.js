// Hyperscript or CDN import for Supabase could be used, but for simplicity we'll assume a CDN script is loaded in the HTML.
const SUPABASE_URL = 'https://cvqqrqdywzxeqqcetptz.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_NJNcYL_hctQVm8Nzp5cG8g_XrJLwkCl';

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

/**
 * Gets the current session and user profile
 */
async function getCurrentUser() {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return null;

    const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', session.user.id)
        .single();

    return { ...session.user, profile };
}

/**
 * Updates the navigation bar based on auth state
 */
async function updateNav() {
    const user = await getCurrentUser();
    const authNav = document.getElementById('auth-nav');
    if (!authNav) return;

    if (user) {
        authNav.innerHTML = `
            <a href="/profile.html" class="nav-link">Profile (${user.profile?.role || 'free'})</a>
            <a href="#" id="logout-btn" class="nav-link">Logout</a>
        `;
        document.getElementById('logout-btn').addEventListener('click', async (e) => {
            e.preventDefault();
            await supabase.auth.signOut();
            window.location.reload();
        });
    } else {
        authNav.innerHTML = `
            <a href="/auth.html" class="nav-link">Login / Sign Up</a>
        `;
    }
}

// Export for use in other scripts if needed, or just expose globally
window.velonowAuth = { 
    supabase, 
    getCurrentUser, 
    updateNav,
    /**
     * Checks if user has access to a resource based on their role
     * @param {string[]} requiredRoles - Roles allowed to see the content
     */
    async checkAccess(requiredRoles) {
        const user = await getCurrentUser();
        const role = user?.profile?.role || 'free';
        
        if (requiredRoles.includes(role)) {
            return { hasAccess: true, user };
        }
        return { hasAccess: false, user };
    },

    /**
     * Utility to protect a page. Hides content and shows gate if unauthorized.
     */
    async protectContent() {
        const premiumSections = document.querySelectorAll('.premium-content');
        const upgradeGate = document.getElementById('upgrade-gate');
        
        const { hasAccess, user } = await this.checkAccess(['subscriber', 'admin']);
        
        if (hasAccess) {
            premiumSections.forEach(s => s.style.display = 'block');
            if (upgradeGate) upgradeGate.style.display = 'none';
        } else {
            premiumSections.forEach(s => s.style.display = 'none');
            if (upgradeGate) upgradeGate.style.display = 'block';
        }
    }
};

// Initialize nav on load
document.addEventListener('DOMContentLoaded', updateNav);
