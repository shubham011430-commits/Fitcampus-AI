const Auth = (() => {
    function redirectIfLogged(dest = "index.html") {
        if (API.isLoggedIn()) window.location.href = dest;
    }
    function requireAuth(dest = "login.html") {
        if (!API.isLoggedIn()) window.location.href = dest;
    }
    function logout() {
        API.clearToken(); API.clearUser();
        window.location.href = "login.html";
    }
    async function refreshUser() {
        try {
            const u = await API.get("/api/profile");
            API.setUser(u); return u;
        } catch (e) { return API.getUser(); }
    }
    return { redirectIfLogged, requireAuth, logout, refreshUser };
})();

// Escape user-controlled text before putting it into innerHTML (prevents XSS)
function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function toast(msg, type = "info") {
    let wrap = document.querySelector(".toast-wrap");
    if (!wrap) { wrap = document.createElement("div"); wrap.className = "toast-wrap"; document.body.appendChild(wrap); }
    const t = document.createElement("div");
    t.className = "toast " + (type === "error" ? "error" : type === "success" ? "success" : "");
    t.textContent = msg; wrap.appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 300); }, 3000);
}

function renderProfileChip(user) {
    const el = document.getElementById("profileChip");
    if (!el || !user) return;
    const initials = (user.name || "U").split(" ").map(s => s[0]).join("").slice(0, 2).toUpperCase();
    el.innerHTML = `
        <div class="avatar">${esc(initials)}</div>
        <div>
            <div class="name">${esc(user.name || "Student")}</div>
            <div class="sub">🔥 ${esc(user.current_streak || 0)} streak • 🏆 #${esc(user.rank || "-")}</div>
        </div>`;
}
