document.addEventListener("DOMContentLoaded", async () => {
    Auth.requireAuth();
    document.getElementById("logoutBtn")?.addEventListener("click", Auth.logout);
    const user = API.getUser() || await Auth.refreshUser();
    if (user) renderProfileChip(user);
    document.querySelectorAll(".period-btn").forEach(b => {
        b.addEventListener("click", () => {
            document.querySelectorAll(".period-btn").forEach(x => { x.classList.remove("btn-primary"); x.classList.add("btn-secondary"); });
            b.classList.remove("btn-secondary"); b.classList.add("btn-primary");
            loadBoard(b.dataset.period);
        });
    });
    await loadBoard("weekly");
});
async function loadBoard(period) {
    const host = document.getElementById("leaderList");
    if (!host) return;
    try {
        const data = await API.get(`/api/leaderboard?period=${encodeURIComponent(period)}`);
        if (!data.entries.length) { host.innerHTML = `<div class="empty-state">No data</div>`; return; }
        host.innerHTML = data.entries.map(e => `
            <div class="leader-row ${e.is_me ? "me" : ""}">
                <div class="rank-badge ${e.rank === 1 ? "rank-1" : e.rank === 2 ? "rank-2" : e.rank === 3 ? "rank-3" : ""}">${esc(e.rank)}</div>
                <div style="font-weight:600">${esc(e.name)} ${e.is_me ? '<span style="background:var(--blue-500);color:#fff;padding:2px 8px;border-radius:999px;font-size:10px;margin-left:6px">YOU</span>' : ""}</div>
                <div style="font-weight:700;color:var(--navy-900)">${esc(e.points)}</div>
                <div>🔥 ${esc(e.streak)}</div>
            </div>`).join("");
    } catch (e) { host.innerHTML = `<div class="empty-state">Failed to load</div>`; }
}
