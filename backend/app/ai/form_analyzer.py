
from typing import Dict, Any


def get_angle(angles: Dict[str, float], *names: str, default: float = 0.0) -> float:
    """Return the first available angle, or default if none is present."""
    for name in names:
        value = angles.get(name)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    return default


def result(feedback: str, score: float, rep_count: int, phase: str) -> Dict[str, Any]:
    return {
        "feedback": feedback,
        "form_score": round(max(0.0, min(100.0, score)), 1),
        "rep_count": rep_count,
        "phase": phase,
    }


def analyze_squat(angles, phase, rep_count):
    knee = get_angle(angles, "left_knee", "right_knee", default=170)
    hip = get_angle(angles, "left_hip", "right_hip", default=170)

    feedback, score = "Good form", 85.0

    if phase == "down":
        if knee > 130:
            feedback, score = "Bend your knees a little more, if comfortable", 65
        elif knee < 70:
            feedback, score = "Use a comfortable depth and stay controlled", 75

        if hip < 60:
            feedback, score = "Check your torso position and keep the movement controlled", 60
    elif knee < 150:
        feedback, score = "Stand up fully to complete the movement", 70

    return result(feedback, score, rep_count, phase)


def analyze_pushup(angles, phase, rep_count):
    elbow = get_angle(angles, "left_elbow", "right_elbow", default=170)

    feedback, score = "Good form", 85.0

    if phase == "down":
        if elbow > 130:
            feedback, score = "Lower your body by bending your elbows, if comfortable", 65
        elif elbow < 60:
            feedback, score = "Avoid forcing the movement; stay controlled", 75
    elif elbow < 150:
        feedback, score = "Push up to a comfortable straight-arm position", 70

    return result(feedback, score, rep_count, phase)


def analyze_lunge(angles, phase, rep_count):
    knee = get_angle(angles, "front_knee", "left_knee", "right_knee", default=0)

    if knee == 0:
        return result("Knee angle unavailable; adjust your camera position", 0, rep_count, phase)

    if phase == "down" and knee > 120:
        return result("Bend your front knee a little more, if comfortable", 65, rep_count, phase)

    return result("Keep your torso steady and move with control", 80, rep_count, phase)


def analyze_bicep_curl(angles, phase, rep_count):
    elbow = get_angle(angles, "left_elbow", "right_elbow", default=0)

    if elbow == 0:
        return result("Elbow angle unavailable; make sure your arm is visible", 0, rep_count, phase)

    if phase == "up" and elbow > 70:
        return result("Curl upward without swinging your body", 70, rep_count, phase)

    if phase == "down" and elbow < 130:
        return result("Lower your arm slowly and with control", 75, rep_count, phase)

    return result("Keep your elbows close to your sides", 85, rep_count, phase)


def analyze_shoulder_press(angles, phase, rep_count):
    elbow = get_angle(angles, "left_elbow", "right_elbow", default=0)

    if elbow == 0:
        return result("Elbow angle unavailable; keep your arm visible", 0, rep_count, phase)

    if phase == "up" and elbow < 145:
        return result("Continue pressing upward without forcing your joints", 70, rep_count, phase)

    if phase == "down" and elbow > 165:
        return result("Lower your arms with control", 75, rep_count, phase)

    return result("Keep the movement controlled and comfortable", 85, rep_count, phase)


def analyze_stretching(angles, phase, rep_count):
    # Generic guidance only: a specific stretch needs its own landmarks and rules.
    if not angles:
        return result(
            "Move into a comfortable position and ensure your body is visible",
            0, rep_count, phase
        )

    return result(
        "Hold a comfortable position, breathe normally, and avoid bouncing",
        80, rep_count, phase
    )


def analyze(req: Dict[str, Any]) -> Dict[str, Any]:
    exercise = str(req.get("exercise", "")).strip().lower().replace("-", "_")
    angles = req.get("angles") or {}
    phase = str(req.get("phase", "up")).lower()
    rep_count = int(req.get("rep_count", 0))

    analyzers = {
        "squat": analyze_squat,
        "pushup": analyze_pushup,
        "lunge": analyze_lunge,
        "lunges": analyze_lunge,
        "bicep_curl": analyze_bicep_curl,
        "shoulder_press": analyze_shoulder_press,
        "stretching": analyze_stretching,
    }

    analyzer = analyzers.get(exercise)
    if analyzer is None:
        return result(
            f"Exercise '{exercise}' is not supported yet",
            0, rep_count, phase
        )

    return analyzer(angles, phase, rep_count)

