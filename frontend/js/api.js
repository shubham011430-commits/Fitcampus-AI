const API = (() => {
    const base = () => window.APP_CONFIG.API_BASE;
    const tokenKey = window.APP_CONFIG.TOKEN_KEY;
    function headers(json = true) {
        const h = {};
        if (json) h["Content-Type"] = "application/json";
        const t = localStorage.getItem(tokenKey);
        if (t) h["Authorization"] = "Bearer " + t;
        return h;
    }
    async function request(method, path, body) {
        const opts = { method, headers: headers() };
        if (body !== undefined) opts.body = JSON.stringify(body);
        let res;
        try { res = await fetch(base() + path, opts); }
        catch (e) { throw new Error("Cannot reach server. Is the backend running on " + base() + "?"); }
        const text = await res.text();
        let data = null;
        try { data = text ? JSON.parse(text) : null; } catch { data = { detail: text }; }
        if (!res.ok) {
            // Expired / invalid token -> clear it so login page doesn't redirect-loop
            if (res.status === 401 && !path.startsWith("/api/auth/")) {
                localStorage.removeItem(tokenKey);
                localStorage.removeItem(window.APP_CONFIG.USER_KEY);
                window.location.href = "login.html";
                throw new Error("Session expired. Please log in again.");
            }
            let msg = data && (data.detail || data.message);
            if (Array.isArray(msg)) msg = msg.map(m => m.msg || JSON.stringify(m)).join("; ");
            throw new Error(msg || ("Error " + res.status));
        }
        return data;
    }
    return {
        get: (p) => request("GET", p),
        post: (p, b) => request("POST", p, b),
        put: (p, b) => request("PUT", p, b),
        del: (p) => request("DELETE", p),
        setToken(t) { localStorage.setItem(tokenKey, t); },
        getToken() { return localStorage.getItem(tokenKey); },
        clearToken() { localStorage.removeItem(tokenKey); },
        setUser(u) { localStorage.setItem(window.APP_CONFIG.USER_KEY, JSON.stringify(u)); },
        getUser() { try { return JSON.parse(localStorage.getItem(window.APP_CONFIG.USER_KEY)); } catch { return null; } },
        clearUser() { localStorage.removeItem(window.APP_CONFIG.USER_KEY); },
        isLoggedIn() { return !!localStorage.getItem(tokenKey); },
    };
})();
