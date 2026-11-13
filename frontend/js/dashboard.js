document.addEventListener("DOMContentLoaded", async () => {
    Auth.requireAuth();
    document.getElementById("logoutBtn")?.addEventListener("click", Auth.logout);
    const cached = API.getUser();
    if (cached) renderProfileChip(cached);

    let d = null;
    try {
        d = await API.get("/api/dashboard");
        renderWelcome(d);
        renderStatCards(d);
        renderYesterday(d.yesterday);
        renderRecommendations(d.recommendations);
        renderTodayProgress(d.today);
        renderProfileChip({ ...(cached || {}), name: d.name, current_streak: d.streak, rank: d.rank });
    } catch (e) { toast("Failed to load dashboard: " + e.message, "error"); }

    initJourneyTracker(d);
});

function renderWelcome(d) {
    const el = document.getElementById("welcomeGreet");
    if (!el) return;
    el.querySelector(".welcome-greet").textContent = `${d.greeting}, ${d.name || "Student"} 👋`;
    el.querySelector(".welcome-sub").textContent = "Let's stay active and keep your streak alive!";
    el.querySelector(".stat-val.s1").textContent = d.streak || 0;
    el.querySelector(".stat-val.s2").textContent = d.points || 0;
    el.querySelector(".stat-val.s3").textContent = "#" + (d.rank || "-");
}
function renderStatCards(d) {
    const y = d.yesterday || {};
    document.getElementById("ySteps").textContent = (y.steps || 0).toLocaleString();
    document.getElementById("yEx").textContent = (y.exercise_minutes || 0) + " min";
    document.getElementById("yCal").textContent = (y.calories || 0) + " kcal";
    document.getElementById("yGoal").textContent = (y.goal_pct || 0) + "%";
}
function renderYesterday(y) {
    const bar = document.getElementById("yesterdayBar");
    if (!bar) return;
    bar.querySelector(".progress-fill").style.width = (y.goal_pct || 0) + "%";
    bar.querySelector(".progress-label .pct").textContent = (y.goal_pct || 0) + "%";
}
function renderRecommendations(recs) {
    const host = document.getElementById("recsList");
    if (!host) return;
    if (!recs || !recs.length) {
        host.innerHTML = `<div class="empty-state"><div class="ico">🎯</div>No recommendations yet. Update your profile!</div>`;
        return;
    }
    host.innerHTML = recs.map((r, i) => `
        <div class="activity-card" data-idx="${i}">
            <div class="activity-head">
                <div class="activity-name">${esc(r.name)}</div>
                <div class="activity-diff diff-${esc(r.difficulty)}">${esc(r.difficulty)}</div>
            </div>
            <div class="activity-desc">${esc(r.desc)}</div>
            <div class="activity-meta">
                <span>⏱️ ${esc(r.duration)} min</span>
                <span>🔥 ${esc(r.calories)} kcal</span>
                <span>🏷️ ${esc(r.type)}</span>
            </div>
            <div class="activity-actions">
                <button class="btn btn-primary btn-sm start-act">Start</button>
                <button class="btn btn-secondary btn-sm complete-act" disabled>Complete</button>
            </div>
        </div>`).join("");

    host.querySelectorAll(".activity-card").forEach((card, i) => {
        const r = recs[i];
        const startBtn = card.querySelector(".start-act");
        const completeBtn = card.querySelector(".complete-act");
        let activityId = null;
        startBtn.addEventListener("click", async () => {
            try {
                startBtn.disabled = true; startBtn.innerHTML = '<span class="loader"></span>';
                const created = await API.post("/api/activities", {
                    activity_type: r.type, duration_minutes: r.duration, calories_estimate: r.calories,
                });
                activityId = created.id;
                startBtn.textContent = "Started ✓";
                completeBtn.disabled = false;
                toast("Activity started! Complete it after doing it 💪", "success");
            } catch (e) { toast(e.message, "error"); startBtn.disabled = false; startBtn.textContent = "Start"; }
        });
        completeBtn.addEventListener("click", async () => {
            if (!activityId) return toast("Start the activity first", "error");
            try {
                completeBtn.disabled = true;
                await API.post(`/api/activities/${activityId}/complete`);
                completeBtn.textContent = "Completed ✓";
                toast("Activity completed! Points earned 🎉", "success");
                setTimeout(() => location.reload(), 800);
            } catch (e) { toast(e.message, "error"); completeBtn.disabled = false; }
        });
    });
}
function renderTodayProgress(t) {
    const circle = document.getElementById("todayCircle");
    if (!circle) return;
    const pct = t.goal_pct || 0;
    circle.style.setProperty("--pct", pct);
    circle.querySelector(".val").textContent = pct + "%";
    document.getElementById("todayMin").textContent = (t.exercise_minutes || 0) + " min";
    document.getElementById("todayDone").textContent = t.completed || 0;
}

// ===== Journey Tracker =====
let journeyState = { mode: "walking", journeyId: null, timerInterval: null, startTime: null, watchId: null, startCoords: null, distanceKm: 0 };

function initJourneyTracker(dash) {
    // Wire up controls first so they always work
    document.querySelectorAll(".mode-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".mode-chip").forEach(c => c.classList.remove("selected"));
            chip.classList.add("selected");
            journeyState.mode = chip.dataset.mode;
        });
    });
    document.getElementById("startJourneyBtn")?.addEventListener("click", startJourney);
    document.getElementById("stopJourneyBtn")?.addEventListener("click", stopJourney);
    document.getElementById("cancelJourneyBtn")?.addEventListener("click", cancelJourney);

    const j = dash && dash.journey;
    if (!j) return;
    if (j.ongoing) {
        journeyState.journeyId = j.ongoing.id;
        journeyState.mode = j.ongoing.mode;
        journeyState.startTime = new Date(j.ongoing.start_time);
        showOngoingJourney();
    } else if (j.today_completed) {
        showCompletedJourney(j.today_completed);
        loadCanteenRec();
    }
}

async function startJourney() {
    const btn = document.getElementById("startJourneyBtn");
    btn.disabled = true; btn.innerHTML = '<span class="loader"></span> Starting...';
    try {
        let startLat = null, startLng = null, startLoc = "Home";
        if (navigator.geolocation) {
            try {
                const pos = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000, enableHighAccuracy: false });
                });
                startLat = pos.coords.latitude; startLng = pos.coords.longitude; startLoc = "Home (GPS)";
            } catch (e) { /* GPS is optional */ }
        }
        const res = await API.post("/api/journey/start", {
            mode: journeyState.mode, start_location: startLoc, start_lat: startLat, start_lng: startLng,
        });
        journeyState.journeyId = res.id;
        journeyState.startTime = new Date();
        journeyState.startCoords = startLat !== null ? { lat: startLat, lng: startLng } : null;
        journeyState.distanceKm = 0;
        if (navigator.geolocation && journeyState.startCoords) {
            journeyState.watchId = navigator.geolocation.watchPosition((pos) => {
                journeyState.distanceKm = haversine(journeyState.startCoords.lat, journeyState.startCoords.lng, pos.coords.latitude, pos.coords.longitude);
                document.getElementById("jDist").textContent = journeyState.distanceKm.toFixed(2);
            }, () => {}, { enableHighAccuracy: false, maximumAge: 10000 });
        }
        showOngoingJourney();
        toast("Journey started! Safe travels 🚶", "success");
    } catch (e) {
        toast("Failed to start: " + e.message, "error");
        btn.disabled = false; btn.textContent = "▶️ Start Journey (Leaving Home)";
    }
}
function showOngoingJourney() {
    document.getElementById("journeyPreStart").classList.add("hidden");
    document.getElementById("journeyCompleted").classList.add("hidden");
    document.getElementById("journeyOngoing").classList.remove("hidden");
    const modeIcons = { walking: "🚶", cycling: "🚴", bus: "🚌", auto: "🛺", own_vehicle: "🏍️" };
    document.getElementById("jMode").textContent = modeIcons[journeyState.mode] || "🚶";
    const status = document.getElementById("journeyStatus");
    status.textContent = "🟢 Journey in progress"; status.classList.add("active");
    startTimer();
}
function startTimer() {
    if (journeyState.timerInterval) clearInterval(journeyState.timerInterval);
    const tick = () => {
        const elapsed = Math.max(0, Math.floor((new Date() - journeyState.startTime) / 1000));
        const m = Math.floor(elapsed / 60).toString().padStart(2, "0");
        const s = (elapsed % 60).toString().padStart(2, "0");
        document.getElementById("jTimer").textContent = `${m}:${s}`;
        document.getElementById("jCal").textContent = estimateJourneyCal(journeyState.mode, elapsed / 60, journeyState.distanceKm);
    };
    tick();
    journeyState.timerInterval = setInterval(tick, 1000);
}
function stopTracking() {
    if (journeyState.watchId !== null && navigator.geolocation) navigator.geolocation.clearWatch(journeyState.watchId);
    if (journeyState.timerInterval) clearInterval(journeyState.timerInterval);
    journeyState.watchId = null; journeyState.timerInterval = null;
}
async function stopJourney() {
    if (!journeyState.journeyId) return;
    const btn = document.getElementById("stopJourneyBtn");
    btn.disabled = true;
    try {
        let endLat = null, endLng = null;
        if (navigator.geolocation && journeyState.startCoords) {
            try {
                const pos = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
                });
                endLat = pos.coords.latitude; endLng = pos.coords.longitude;
            } catch (e) {}
        }
        const res = await API.post(`/api/journey/${journeyState.journeyId}/stop`, {
            end_location: "College", end_lat: endLat, end_lng: endLng,
            distance_km: journeyState.distanceKm > 0 ? journeyState.distanceKm : null,
        });
        stopTracking();
        showCompletedJourney(res.journey);
        toast(res.message, "success");
        loadCanteenRec();
        const u = await Auth.refreshUser(); if (u) renderProfileChip(u);
    } catch (e) { toast("Failed to stop: " + e.message, "error"); btn.disabled = false; }
}
async function cancelJourney() {
    if (!confirm("Cancel this journey? No points will be awarded.")) return;
    try { await API.post(`/api/journey/${journeyState.journeyId}/cancel`); } catch (e) {}
    stopTracking();
    resetJourneyUI();
    toast("Journey cancelled", "info");
}
function showCompletedJourney(j) {
    document.getElementById("journeyPreStart").classList.add("hidden");
    document.getElementById("journeyOngoing").classList.add("hidden");
    document.getElementById("journeyCompleted").classList.remove("hidden");
    document.getElementById("jcDur").textContent = j.duration_minutes || 0;
    document.getElementById("jcDist").textContent = (j.distance_km || 0).toFixed(1);
    document.getElementById("jcSteps").textContent = j.steps_estimate || 0;
    document.getElementById("jcCal").textContent = j.calories_burned || 0;
    const status = document.getElementById("journeyStatus");
    status.textContent = "✅ Completed today"; status.classList.add("active");
}
function resetJourneyUI() {
    journeyState = { mode: "walking", journeyId: null, timerInterval: null, startTime: null, watchId: null, startCoords: null, distanceKm: 0 };
    document.getElementById("journeyPreStart").classList.remove("hidden");
    document.getElementById("journeyOngoing").classList.add("hidden");
    document.getElementById("journeyCompleted").classList.add("hidden");
    document.querySelectorAll(".mode-chip").forEach(c => c.classList.toggle("selected", c.dataset.mode === "walking"));
    const status = document.getElementById("journeyStatus");
    status.textContent = "⏸️ Not Started"; status.classList.remove("active");
    const btn = document.getElementById("startJourneyBtn");
    btn.disabled = false; btn.textContent = "▶️ Start Journey (Leaving Home)";
    document.getElementById("stopJourneyBtn").disabled = false;
}
function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
function estimateJourneyCal(mode, mins, km) {
    const met = { walking: 3.8, cycling: 6.0, bus: 1.3, auto: 1.0, own_vehicle: 1.2 }[mode] || 2.0;
    let cal = met * 70 * (mins / 60);
    if ((mode === "walking" || mode === "cycling") && km > 0) cal += km * 30;
    return Math.round(cal);
}
async function loadCanteenRec() {
    const host = document.getElementById("canteenContent");
    if (!host) return;
    try {
        const rec = await API.get("/api/journey/canteen-recommendation");
        host.innerHTML = `
            <div style="font-size:13px; color:var(--gray-500); margin-bottom:12px;">🎯 <b>${esc(rec.category)}</b> — based on your fitness goal</div>
            <div style="font-size:12px; font-weight:700; color:var(--navy-900); margin-bottom:8px;">✨ Recommended:</div>
            ${rec.recommended.map(foodItemHTML).join("")}
            ${rec.side_options && rec.side_options.length ? `
                <div style="font-size:12px; font-weight:700; color:var(--navy-900); margin:12px 0 8px;">🥗 Good Side Options:</div>
                ${rec.side_options.map(foodItemHTML).join("")}` : ""}
            <div class="hydration-tip">💧 ${esc(rec.hydration_tip)}</div>
            ${rec.avoid && rec.avoid.length ? `
                <div class="avoid-list">
                    <div class="title">Try to Avoid:</div>
                    <ul>${rec.avoid.map(a => `<li>${esc(a)}</li>`).join("")}</ul>
                </div>` : ""}
            ${rec.tips && rec.tips.length ? `
                <div style="margin-top:12px; padding:10px 14px; background:var(--gray-50); border-radius:var(--radius-md);">
                    <div style="font-size:12px; font-weight:700; color:var(--navy-900); margin-bottom:6px;">💡 Tips:</div>
                    <ul style="list-style:none; padding:0; margin:0;">
                        ${rec.tips.map(t => `<li style="font-size:12.5px; color:var(--gray-700); padding:2px 0;">✅ ${esc(t)}</li>`).join("")}
                    </ul>
                </div>` : ""}
            <div style="font-size:11px; color:var(--gray-500); margin-top:10px; font-style:italic;">⚠️ ${esc(rec.disclaimer)}</div>`;
    } catch (e) { host.innerHTML = `<div class="empty-state">Failed to load recommendations</div>`; }
}
function foodItemHTML(f) {
    return `
        <div class="food-item">
            <div>
                <div class="food-name">${esc(f.tag)} ${esc(f.name)}</div>
                <div class="food-meta">~${esc(f.cal)} kcal • ${esc(f.protein)} protein</div>
            </div>
            <div class="food-price">₹${esc(f.price)}</div>
        </div>`;
}
