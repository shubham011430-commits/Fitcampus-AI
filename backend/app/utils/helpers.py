from datetime import datetime, date, timedelta


def today_str() -> str:
    return date.today().isoformat()


def yesterday_str() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def greeting() -> str:
    h = datetime.now().hour
    if 5 <= h < 12:
        return "Good Morning"
    if 12 <= h < 17:
        return "Good Afternoon"
    if 17 <= h < 21:
        return "Good Evening"
    return "Good Night"


def estimate_calories(activity_type: str, duration_minutes: int) -> int:
    met = {
        "walking": 3.5, "running": 7.0, "stretching": 2.3,
        "sports": 6.0, "yoga": 2.5, "general": 3.0,
    }.get(activity_type, 3.0)
    return int(met * 70 * (duration_minutes / 60.0))


def points_for_activity(duration_minutes: int) -> int:
    return max(5, duration_minutes // 2)
