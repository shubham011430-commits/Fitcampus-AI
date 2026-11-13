document.addEventListener("DOMContentLoaded", async () => {
    Auth.requireAuth();
    const user = API.getUser() || await Auth.refreshUser();
    if (user) renderProfileChip(user);
    document.getElementById("logoutBtn")?.addEventListener("click", Auth.logout);

    await checkActiveSession();
    await loadTodaySessions();
    await loadSessionHistory();

    document.getElementById("startSessionBtn")?.addEventListener("click", startSession);
    document.getElementById("stopSessionBtn")?.addEventListener("click", stopSession);
});

let activeSession = null;
let timerInterval = null;
let sessionStartTime = null;

async function checkActiveSession() {
    try {
        const res = await API.get("/api/sessions/active");
        if (res.active) {
            activeSession = res.active;
            sessionStartTime = new Date(res.active.start_time);
            showActiveUI(res.active);
            startTimer();
        }
    } catch (e) {
        console.warn("Session check failed", e);
    }
}

function showActiveUI(session) {
    document.getElementById("startSessionBtn").classList.add("hidden");
    document.getElementById("stopSessionBtn").classList.remove("hidden");
    document.getElementById("activityPicker").classList.add("hidden");
    document.getElementById("sessionBadge").classList.remove("hidden");
    document.getElementById("sessionTimer").classList.add("active");
    document.getElementById("sessionStatus").textContent = `Tracking: ${session.activity_type}`;
    document.getElementById("tType").textContent = session.activity_type;
}

function showIdleUI() {
    document.getElementById("startSessionBtn").classList.remove("hidden");
    document.getElementById("stopSessionBtn").classList.add("hidden");
    document.getElementById("activityPicker").classList.remove("hidden");
    document.getElementById("sessionBadge").classList.add("hidden");
    document.getElementById("sessionTimer").classList.remove("active");
    document.getElementById("sessionTimer").textContent = "00:00:00";
    document.getElementById("sessionStatus").textContent = "No active session";
    document.getElementById("tType").textContent = "—";
    document.getElementById("tCalories").textContent = "0";
    document.getElementById("tSteps").textContent = "0";
}

function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((new Date() - sessionStartTime) / 1000);
        const h = Math.floor(elapsed / 3600).toString().padStart(2, "0");
        const m = Math.floor((elapsed % 3600) / 60).toString().padStart(2, "0");
        const s = (elapsed % 60).toString().padStart(2, "0");
        document.getElementById("sessionTimer").textContent = `${h}:${m}:${s}`;

        // Estimate calories
        const mins = elapsed / 60;
        const type = activeSession?.activity_type || "general";
        const met = { walking: 3.5, running: 7.0, cycling: 6.0, yoga: 2.5, sports: 6.0, general: 3.0 }[type] || 3.0;
        const cal = Math.round(met * 70 * (mins / 60));
        document.getElementById("tCalories").textContent = cal;

        // Estimate steps (for walking/running only)
        if (type === "walking") {
            document.getElementById("tSteps").textContent = Math.round(mins * 100);
        } else if (type === "running") {
            document.getElementById("tSteps").textContent = Math.round(mins * 160);
        }
    }, 1000);
}

async function startSession() {
    const btn = document.getElementById("startSessionBtn");
    btn.disabled = true;
    btn.innerHTML = '<span class="loader"></span>';
    try {
        const type = document.getElementById("sessionType").value;
        const res = await API.post("/api/sessions/start", { activity_type: type });
        activeSession = res;
        sessionStartTime = new Date(res.start_time);
        showActiveUI(res);
        startTimer();
        toast("Activity started! Stay consistent 💪", "success");
        await loadTodaySessions();
    } catch (e) {
        toast(e.message, "error");
    } finally {
        btn.disabled = false;
        btn.textContent = "▶ Start Activity";
    }
}

async function stopSession() {
    if (!activeSession) return;
    if (!confirm("Stop this activity session?")) return;
    const btn = document.getElementById("stopSessionBtn");
    btn.disabled = true;
    try {
        const res = await API.post(`/api/sessions/${activeSession.id}/stop`, {
            steps_count: parseInt(document.getElementById("tSteps").textContent) || 0,
        });
        if (timerInterval) clearInterval(timerInterval);
        activeSession = null;
        sessionStartTime = null;
        showIdleUI();
        toast(`Session completed! +${res.points_earned || 0} points 🎉`, "success");
        await loadTodaySessions();
        await loadSessionHistory();
    } catch (e) {
        toast(e.message, "error");
        btn.disabled = false;
    }
}

async function loadTodaySessions() {
    const host = document.getElementById("todaySessions");
    if (!host) return;
    try {
        const list = await API.get("/api/sessions/today");
        if (!list.length) {
            host.innerHTML = `<div class="empty-state"><div class="ico">🏃</div>No sessions today. Start one above!</div>`;
            return;
        }
        host.innerHTML = list.map(s => `
            <div class="activity-card" style="margin-bottom:10px;">
                <div class="activity-head">
                    <div class="activity-name">${s.activity_type}</div>
                    <div class="activity-diff ${s.status === 'completed' ? 'diff-easy' : s.status === 'active' ? 'diff-medium' : 'diff-hard'}">${s.status}</div>
                </div>
                <div class="activity-meta">
                    <span>⏱️ ${Math.floor(s.duration_seconds / 60)} min</span>
                    <span>🔥 ${s.calories_estimate} kcal</span>
                    <span>👣 ${s.steps_count} steps</span>
                </div>
            </div>
        `).join("");
    } catch (e) {
        host.innerHTML = `<div class="empty-state">Failed to load</div>`;
    }
}

async function loadSessionHistory() {
    const host = document.getElementById("sessionHistory");
    if (!host) return;
    try {
        const list = await API.get("/api/sessions/history?limit=10");
        if (!list.length) {
            host.innerHTML = `<div class="empty-state"><div class="ico">📜</div>No history yet.</div>`;
            return;
        }
        host.innerHTML = list.slice(0, 8).map(s => `
            <div style="padding:8px 0; border-bottom:1px solid var(--gray-100); display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:600; font-size:13px;">${s.activity_type}</div>
                    <div style="font-size:11px; color:var(--gray-500);">${new Date(s.start_time).toLocaleString()}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:700; font-size:13px;">${Math.floor(s.duration_seconds / 60)} min</div>
                    <div style="font-size:11px; color:var(--gray-500);">${s.calories_estimate} kcal</div>
                </div>
            </div>
        `).join("");
    } catch (e) {
        host.innerHTML = `<div class="empty-state">Failed to load</div>`;
    }
}