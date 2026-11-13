document.addEventListener("DOMContentLoaded", async () => {
    Auth.requireAuth();
    document.getElementById("logoutBtn")?.addEventListener("click", Auth.logout);
    const user = API.getUser() || await Auth.refreshUser();
    if (user) renderProfileChip(user);
    await loadChallenges();
});
async function loadChallenges() {
    const host = document.getElementById("challengeList");
    if (!host) return;
    try {
        const list = await API.get("/api/challenges");
        if (!list.length) { host.innerHTML = `<div class="empty-state">No challenges yet.</div>`; return; }
        host.innerHTML = list.map(c => `
            <div class="challenge-card">
                <div class="challenge-title">${esc(c.title)}</div>
                <div class="challenge-desc">${esc(c.description)}</div>
                <div class="challenge-meta">
                    <span>📅 ${esc(c.start_date)} → ${esc(c.end_date)}</span>
                    <span>👥 ${esc(c.participants)} joined</span>
                    <span>🏆 ${esc(c.reward_points)} pts</span>
                </div>
                ${c.joined ? `
                    <div class="progress-wrap">
                        <div class="progress-bar"><div class="progress-fill" style="width:${Number(c.progress) || 0}%"></div></div>
                        <div class="progress-label"><span>Progress</span><span class="pct">${Number(c.progress) || 0}%</span></div>
                    </div>
                    <div class="mt-2 text-sm" style="padding:4px 0">${c.completed ? "✅ Completed!" : "In progress"}</div>
                    ${c.completed ? "" : `<div class="flex gap-2 mt-2">
                        <button class="btn btn-secondary btn-sm prog-btn" data-id="${c.id}" data-val="${Math.min(100, (Number(c.progress) || 0) + 25)}">+25% progress</button>
                    </div>`}
                ` : `<button class="btn btn-primary btn-sm join-btn" data-id="${c.id}">Join Challenge</button>`}
            </div>`).join("");
        host.querySelectorAll(".join-btn").forEach(b => {
            b.addEventListener("click", async () => {
                try {
                    await API.post(`/api/challenges/${b.dataset.id}/join`);
                    toast("Joined challenge!", "success");
                    await loadChallenges();
                } catch (e) { toast(e.message, "error"); }
            });
        });
        host.querySelectorAll(".prog-btn").forEach(b => {
            b.addEventListener("click", async () => {
                try {
                    const r = await API.post(`/api/challenges/${b.dataset.id}/progress`, { progress: parseInt(b.dataset.val) });
                    toast(r.completed ? "Challenge completed! 🏆 Reward added" : "Progress updated", "success");
                    await loadChallenges();
                    const u = await Auth.refreshUser(); if (u) renderProfileChip(u);
                } catch (e) { toast(e.message, "error"); }
            });
        });
    } catch (e) { host.innerHTML = `<div class="empty-state">Failed to load</div>`; }
}
