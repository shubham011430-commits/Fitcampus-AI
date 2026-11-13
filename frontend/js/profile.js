document.addEventListener("DOMContentLoaded", async () => {
    Auth.requireAuth();
    let user = await Auth.refreshUser();
    if (user) { API.setUser(user); renderProfile(user); }
    document.getElementById("logoutBtn")?.addEventListener("click", Auth.logout);

    document.getElementById("profileForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const allergiesRaw = document.getElementById("pAllergies").value;
        const allergies = allergiesRaw
            ? allergiesRaw.split(",").map(s => s.trim().toLowerCase()).filter(Boolean)
            : [];
        const body = {
            name: document.getElementById("pName").value,
            student_type: document.getElementById("pStudentType").value,
            age: parseInt(document.getElementById("pAge").value) || null,
            weight: parseFloat(document.getElementById("pWeight").value) || null,
            height: parseFloat(document.getElementById("pHeight").value) || null,
            body_type: document.getElementById("pBodyType").value || null,
            fitness_level: document.getElementById("pFitLevel").value,
            activity_level: document.getElementById("pActLevel").value,
            fitness_goal: document.getElementById("pGoal").value,
            dietary_preference: document.getElementById("pDietPref").value,
            allergies: allergies,
        };
        try {
            const updated = await API.put("/api/profile", body);
            API.setUser(updated);
            renderProfile(updated);
            toast("Profile updated! 🎉", "success");
        } catch (e) { toast(e.message, "error"); }
    });
});

function renderProfile(u) {
    const initials = (u.name || "U").split(" ").map(s => s[0]).join("").slice(0, 2).toUpperCase();
    document.getElementById("profileAvatar").textContent = initials;
    document.getElementById("profileName").textContent = u.name || "Student";
    document.getElementById("profileStreak").textContent = `🔥 ${u.current_streak || 0} Day Streak`;
    document.getElementById("profileRank").textContent = `🏆 Campus Rank #${u.rank || "-"}`;
    document.getElementById("profilePoints").textContent = `⭐ ${u.points || 0} Points`;

    document.getElementById("pName").value = u.name || "";
    document.getElementById("pStudentType").value = u.student_type || "day_scholar";
    document.getElementById("pAge").value = u.age || "";
    document.getElementById("pWeight").value = u.weight || "";
    document.getElementById("pHeight").value = u.height || "";
    document.getElementById("pBodyType").value = u.body_type || "";
    document.getElementById("pFitLevel").value = u.fitness_level || "beginner";
    document.getElementById("pActLevel").value = u.activity_level || "low";
    document.getElementById("pGoal").value = u.fitness_goal || "general_wellness";
    document.getElementById("pDietPref").value = u.dietary_preference || "veg";
    document.getElementById("pAllergies").value = (u.allergies || []).join(", ");
}