document.addEventListener("DOMContentLoaded", async () => {
    Auth.requireAuth();
    document.getElementById("logoutBtn")?.addEventListener("click", Auth.logout);
    const user = (await Auth.refreshUser()) || API.getUser();
    if (user) {
        renderProfileChip(user);
        document.getElementById("dietGoal").value = user.fitness_goal || "general_wellness";
    }
    await loadDiet();
    document.getElementById("personalizeBtn")?.addEventListener("click", async () => {
        const goal = document.getElementById("dietGoal").value;
        try {
            await API.post("/api/diet/personalize", { preferences: { fitness_goal: goal } });
            toast("Diet personalized!", "success");
            await Auth.refreshUser();
            await loadDiet();
        } catch (e) { toast(e.message, "error"); }
    });
});
async function loadDiet() {
    const host = document.getElementById("dietContent");
    if (!host) return;
    try {
        const d = await API.get("/api/diet/recommendation");
        host.innerHTML = `
            <div class="card mb-3">
                <div class="card-title">🎯 Daily Target <span class="badge">${esc(d.daily_calories_target)} kcal</span></div>
                <div class="text-sm text-muted">${esc(d.hydration)}</div>
            </div>
            <div class="grid grid-2">
                ${mealCard("🌅 Breakfast", d.breakfast)}
                ${mealCard("☀️ Lunch", d.lunch)}
                ${mealCard("🌙 Dinner", d.dinner)}
                ${mealCard("🍎 Snacks", d.snacks)}
            </div>
            <div class="card mt-3">
                <div class="card-title">📌 Notes</div>
                <ul class="meal-list">${d.notes.map(n => `<li>${esc(n)}</li>`).join("")}</ul>
                <div class="text-sm text-muted mt-2">⚠️ General wellness suggestions only — not medical advice.</div>
            </div>`;
    } catch (e) { host.innerHTML = `<div class="empty-state">Failed to load diet: ${esc(e.message)}</div>`; }
}
function mealCard(title, items) {
    return `<div class="meal-card">
        <div class="meal-title">${title}</div>
        <ul class="meal-list">${items.map(i => `<li>${esc(i)}</li>`).join("")}</ul>
    </div>`;
}
