# FitCampus AI — Upgraded v2.0

**AI-Powered Student Fitness Platform with Hostel/Canteen Integration**

## 🎯 Key Features
1. **Hosteler / Day Scholar Registration** — Different menus based on student type
2. **Hostel Mess Menu** — Breakfast/Lunch/Snacks/Dinner with nutrition info
3. **College Canteen Menu** — Filterable by meal type & category, with prices
4. **Activity Tracking (Start/Stop)** — Live timer, calories, steps
5. **AI Exercise Form Detection** — Browser-based MediaPipe pose analysis
6. **Gemini AI Diet Recommendations** — With rule-based fallback
7. **Allergy-aware Recommendations** — Never suggests allergens
8. **Modern Animated UI** — Dark navy theme with glassmorphism
9. **Gamification** — Points, streaks, leaderboard, challenges

## 🛠️ Tech Stack
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3.10, FastAPI, SQLAlchemy (async)
- **Database**: MySQL 8.0+
- **AI**: Google Gemini API (optional) + rule-based fallback
- **CV**: MediaPipe JS (browser-based pose detection)

## 📦 Setup Instructions

### 1. Prerequisites
- **Python 3.10** (3.11 works; 3.12+ has compatibility issues)
- **MySQL 8.0+** (local or cloud)
- Modern browser (Chrome/Edge recommended)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt