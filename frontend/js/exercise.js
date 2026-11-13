document.addEventListener("DOMContentLoaded", async () => {
    Auth.requireAuth();
    document.getElementById("logoutBtn")?.addEventListener("click", Auth.logout);
    const user = API.getUser() || await Auth.refreshUser();
    if (user) renderProfileChip(user);
    await loadExercises();
    document.getElementById("startFormCheck")?.addEventListener("click", startFormCheck);
    document.getElementById("stopFormCheck")?.addEventListener("click", stopFormCheck);
});
window.addEventListener("beforeunload", () => { if (cameraObj) { try { cameraObj.stop(); } catch (e) {} } });

async function loadExercises() {
    const host = document.getElementById("exerciseList");
    if (!host) return;
    try {
        const list = await API.get("/api/exercises");
        host.innerHTML = list.map(e => `
            <div class="activity-card">
                <div class="activity-head">
                    <div class="activity-name">${esc(e.name)}</div>
                    <div class="activity-diff diff-${esc(e.difficulty)}">${esc(e.difficulty)}</div>
                </div>
                <div class="activity-desc">${esc(e.desc)}</div>
                <div class="activity-meta"><span>${e.reps ? esc(e.reps) + " reps" : esc(e.duration_sec) + " sec"}</span></div>
                <button class="btn btn-primary btn-sm exercise-select" data-name="${esc(e.name.toLowerCase().replace(/[- ]/g, ""))}">Select for Form Check</button>
            </div>`).join("");
        host.querySelectorAll(".exercise-select").forEach(btn => {
            btn.addEventListener("click", () => selectExercise(btn.dataset.name));
        });
    } catch (e) { host.innerHTML = `<div class="empty-state">Failed to load exercises</div>`; }
}

let currentExercise = "squat", videoEl, canvasEl, ctx, poseInstance = null, cameraObj = null;
let repCount = 0, phase = "up", formScoreSum = 0, formScoreCount = 0, running = false, analyzeTimer = null;
let lastAngles = {};


function selectExercise(name) {
    if (running) {
        return toast("Stop the current form check first", "error");
    }

    const normalized = name.toLowerCase().replace(/[-_\s]/g, "");

    const exerciseMap = {
        squat: "squat",
        squats: "squat",
        pushup: "pushup",
        pushups: "pushup",
        lunge: "lunge",
        lunges: "lunge",
        bicepcurl: "bicep_curl",
        shoulderpress: "shoulder_press",
        stretching: "stretching"
    };

    if (!exerciseMap[normalized]) {
        return toast("This exercise does not have live form detection yet.", "info");
    }

    currentExercise = exerciseMap[normalized];

    const labels = {
        squat: "Squat",
        pushup: "Push-up",
        lunge: "Lunge",
        bicep_curl: "Bicep Curl",
        shoulder_press: "Shoulder Press",
        stretching: "Stretching"
    };

    document.getElementById("selectedExercise").textContent =
        labels[currentExercise];

    toast(`Selected: ${labels[currentExercise]}`, "success");
}


function loadScript(src) {
    return new Promise((resolve, reject) => {
        const s = document.createElement("script");
        s.src = src; s.onload = resolve; s.onerror = () => reject(new Error("Failed to load " + src));
        document.head.appendChild(s);
    });
}

async function startFormCheck() {
    if (running) return;
    videoEl = document.getElementById("videoEl");
    canvasEl = document.getElementById("canvasEl");
    ctx = canvasEl.getContext("2d");
    canvasEl.width = 640; canvasEl.height = 480;
    const overlay = document.getElementById("cameraOverlay");
    overlay.classList.remove("hidden"); overlay.textContent = "Loading pose model…";

    try {
        if (!window.Pose) {
            await loadScript("https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js");
            await loadScript("https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js");
            await loadScript("https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js");
        }
    } catch (e) { overlay.textContent = "Could not load pose model (check internet)"; return toast(e.message, "error"); }

    poseInstance = new window.Pose({ locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${f}` });
    poseInstance.setOptions({ modelComplexity: 1, smoothLandmarks: true, enableSegmentation: false,
        minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
    poseInstance.onResults(onPoseResults);

    running = true; repCount = 0; phase = "up"; formScoreSum = 0; formScoreCount = 0; lastAngles = {};
    // Camera utility owns the single camera stream (no duplicate getUserMedia)
    cameraObj = new window.Camera(videoEl, {
        onFrame: async () => { if (running && poseInstance) await poseInstance.send({ image: videoEl }); },
        width: 640, height: 480,
    });
    try {
        await cameraObj.start();
    } catch (e) {
        running = false; cameraObj = null;
        overlay.textContent = "Camera access denied";
        return toast("Camera access denied", "error");
    }
    overlay.classList.add("hidden");
    analyzeTimer = setInterval(sendToServer, 1500);
    toast("Form check started — perform the exercise in view", "success");
}

async function stopFormCheck() {
    if (!running) return;
    running = false;
    clearInterval(analyzeTimer); analyzeTimer = null;
    if (cameraObj) { try { cameraObj.stop(); } catch (e) {} cameraObj = null; }
    if (videoEl && videoEl.srcObject) { videoEl.srcObject.getTracks().forEach(t => t.stop()); videoEl.srcObject = null; }
    if (poseInstance) { try { poseInstance.close(); } catch (e) {} poseInstance = null; }
    const overlay = document.getElementById("cameraOverlay");
    overlay.classList.remove("hidden"); overlay.textContent = "Camera stopped";
    await saveExercise();
    repCount = 0; formScoreSum = 0; formScoreCount = 0;
}


function onPoseResults(results) {
    if (!running) return;

    ctx.save();
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
    ctx.translate(canvasEl.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(results.image, 0, 0, canvasEl.width, canvasEl.height);

    if (results.poseLandmarks) {
        const lm = results.poseLandmarks;

        window.drawConnectors(
            ctx, lm, window.POSE_CONNECTIONS,
            { color: "#3b82f6", lineWidth: 3 }
        );
        window.drawLandmarks(
            ctx, lm,
            { color: "#ef4444", lineWidth: 1, radius: 3 }
        );

        const visible = (i) => lm[i] && (lm[i].visibility ?? 1) > 0.5;
        const angles = {};
        let primaryAngle = null;
        let angleName = "";

        // Squat: hip-knee-ankle angle
        if (currentExercise === "squat") {
            if (visible(23) && visible(25) && visible(27)) {
                primaryAngle = computeAngle(lm[23], lm[25], lm[27]);
                angles.left_knee = primaryAngle;
                angleName = "knee";
            }
        }

        // Push-up: shoulder-elbow-wrist angle
        else if (currentExercise === "pushup") {
            if (visible(11) && visible(13) && visible(15)) {
                primaryAngle = computeAngle(lm[11], lm[13], lm[15]);
                angles.left_elbow = primaryAngle;
                angleName = "elbow";
            }
        }

        // Lunge: front knee angle (approximation using left leg)
        else if (currentExercise === "lunge") {
            if (visible(23) && visible(25) && visible(27)) {
                primaryAngle = computeAngle(lm[23], lm[25], lm[27]);
                angles.left_knee = primaryAngle;
                angles.front_knee = primaryAngle;
                angleName = "knee";
            }
        }

        // Bicep curl: elbow angle
        else if (currentExercise === "bicep_curl") {
            if (visible(11) && visible(13) && visible(15)) {
                primaryAngle = computeAngle(lm[11], lm[13], lm[15]);
                angles.left_elbow = primaryAngle;
                angleName = "elbow";
            }
        }

        // Shoulder press: elbow angle
        else if (currentExercise === "shoulder_press") {
            if (visible(11) && visible(13) && visible(15)) {
                primaryAngle = computeAngle(lm[11], lm[13], lm[15]);
                angles.left_elbow = primaryAngle;
                angleName = "elbow";
            }
        }

        lastAngles = angles;

        // Stretching does not use rep-count logic.
        if (currentExercise === "stretching") {
            document.getElementById("feedbackText").textContent =
                "Hold a comfortable stretch, breathe normally, and avoid bouncing.";
            document.getElementById("phaseLabel").textContent = "Stretch";
        } else if (primaryAngle === null) {
            document.getElementById("feedbackText").textContent =
                "Body joint not visible. Move back and keep your body in frame.";
        } else {
            if (phase === "up" && primaryAngle < 110) {
                phase = "down";
            } else if (phase === "down" && primaryAngle > 160) {
                phase = "up";
                repCount++;
            }

            document.getElementById("feedbackText").textContent =
                feedbackFor(primaryAngle);

            document.getElementById("phaseLabel").textContent =
                phase === "up" ? "Up" : "Down";
        }

        const score = primaryAngle === null ? 0 : 80;
        if (primaryAngle !== null) {
            formScoreSum += score;
            formScoreCount++;
        }

        document.getElementById("repCount").textContent = repCount;
        document.getElementById("formScore").textContent =
            Math.round(formScoreSum / Math.max(1, formScoreCount));
    }

    ctx.restore();
}

function computeAngle(a, b, c) {
    const ba = { x: a.x - b.x, y: a.y - b.y };
    const bc = { x: c.x - b.x, y: c.y - b.y };
    const dot = ba.x * bc.x + ba.y * bc.y;
    const mag = Math.hypot(ba.x, ba.y) * Math.hypot(bc.x, bc.y);
    if (mag === 0) return 0;
    return Math.acos(Math.max(-1, Math.min(1, dot / mag))) * 180 / Math.PI;
}

function feedbackFor(angle) {
    if (currentExercise === "squat" || currentExercise === "lunge") {
        if (phase === "down" && angle > 130) {
            return "Bend your knees a little more, if comfortable.";
        }
        if (phase === "down" && angle < 70) {
            return "Use a comfortable depth and stay controlled.";
        }
        if (phase === "up" && angle < 150) {
            return "Straighten your legs comfortably to finish the rep.";
        }
        return currentExercise === "lunge"
            ? "Keep your torso steady and move with control."
            : "Keep your torso steady and use a comfortable depth.";
    }

    if (currentExercise === "pushup") {
        if (phase === "down" && angle > 130) {
            return "Bend your elbows more, if comfortable.";
        }
        if (phase === "down") {
            return "Keep your body aligned and move with control.";
        }
        if (angle < 150) {
            return "Push up to a comfortable arm position.";
        }
        return "Good. Lower your body with control.";
    }

    if (currentExercise === "bicep_curl") {
        if (phase === "down" && angle < 130) {
            return "Lower your arm slowly and with control.";
        }
        if (phase === "up" && angle > 70) {
            return "Curl your arm without swinging your body.";
        }
        return "Keep your elbow close to your side.";
    }

    if (currentExercise === "shoulder_press") {
        if (phase === "up" && angle < 145) {
            return "Continue pressing upward without forcing your joints.";
        }
        return "Move your arms with control and keep the movement comfortable.";
    }

    return "Keep the movement comfortable and controlled.";
}

async function sendToServer() {
    if (!running) return;
    try {
        const avgScore = formScoreCount ? Math.round(formScoreSum / formScoreCount) : 0;
        await API.post("/api/form/analyze", {
            exercise: currentExercise, landmarks: [], angles: lastAngles,
            phase: phase, rep_count: repCount, form_score: avgScore,
        });
    } catch (e) { /* periodic snapshot; ignore transient errors */ }
}
async function saveExercise() {
    const avgScore = formScoreCount ? Math.round(formScoreSum / formScoreCount) : 0;
    if (repCount < 1) return toast("No reps detected — nothing saved", "info");
    try {
        const res = await API.post("/api/exercises/complete", {
            exercise_name: currentExercise === "squat" ? "Squats" : "Push-ups",
            repetitions: repCount, duration_seconds: 60, form_score: avgScore,
        });
        toast(`Saved ${repCount} reps! +${res.points_earned} pts 🎉`, "success");
    } catch (e) { toast("Failed to save: " + e.message, "error"); }
}
