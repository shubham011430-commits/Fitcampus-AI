import asyncio
import os
import sys
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from app.config import settings
from app.models import Base, User, Activity, Challenge, MenuItem

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS = [
    {"name": "Demo Student", "email": "demo@fitcampus.com", "password": "demo1234",
     "student_type": "day_scholar", "age": 20, "weight": 68, "height": 172,
     "body_type": "average", "fitness_level": "intermediate", "activity_level": "moderate",
     "fitness_goal": "improve_fitness", "dietary_preference": "veg", "allergies": [],
     "points": 2450, "current_streak": 12, "longest_streak": 21},
    {"name": "Aarav Sharma", "email": "aarav@fitcampus.com", "password": "demo1234",
     "student_type": "hosteler", "age": 21, "weight": 72, "height": 178,
     "body_type": "athletic", "fitness_level": "advanced", "activity_level": "high",
     "fitness_goal": "build_strength", "dietary_preference": "non_veg", "allergies": [],
     "points": 3120, "current_streak": 18, "longest_streak": 30},
    {"name": "Priya Patel", "email": "priya@fitcampus.com", "password": "demo1234",
     "student_type": "day_scholar", "age": 19, "weight": 58, "height": 162,
     "body_type": "slim", "fitness_level": "beginner", "activity_level": "low",
     "fitness_goal": "stay_active", "dietary_preference": "veg", "allergies": ["peanuts"],
     "points": 1280, "current_streak": 5, "longest_streak": 14},
    {"name": "Rohan Verma", "email": "rohan@fitcampus.com", "password": "demo1234",
     "student_type": "hosteler", "age": 22, "weight": 75, "height": 180,
     "body_type": "broad", "fitness_level": "advanced", "activity_level": "very_high",
     "fitness_goal": "improve_endurance", "dietary_preference": "eggetarian", "allergies": [],
     "points": 2980, "current_streak": 22, "longest_streak": 40},
    {"name": "Ananya Iyer", "email": "ananya@fitcampus.com", "password": "demo1234",
     "student_type": "day_scholar", "age": 20, "weight": 60, "height": 165,
     "body_type": "average", "fitness_level": "intermediate", "activity_level": "moderate",
     "fitness_goal": "general_wellness", "dietary_preference": "vegan", "allergies": ["dairy"],
     "points": 1850, "current_streak": 9, "longest_streak": 18},
]

CHALLENGES = [
    {"title": "7-Day Walking Challenge", "description": "Walk at least 6,000 steps every day for a week.",
     "start_date": date.today().isoformat(), "end_date": (date.today() + timedelta(days=7)).isoformat(),
     "reward_points": 200, "participants": 42},
    {"title": "30-Day Fitness Challenge", "description": "Complete at least 30 minutes of activity every day for a month.",
     "start_date": date.today().isoformat(), "end_date": (date.today() + timedelta(days=30)).isoformat(),
     "reward_points": 800, "participants": 128},
    {"title": "Weekly Exercise Challenge", "description": "Complete 5 workouts this week.",
     "start_date": date.today().isoformat(), "end_date": (date.today() + timedelta(days=7)).isoformat(),
     "reward_points": 150, "participants": 76},
]

# Hostel Mess Menu
HOSTEL_MESS = [
    {"menu_type": "hostel_mess", "meal_type": "breakfast", "name": "Poha", "category": "veg",
     "calories": 250, "protein_g": 6, "carbs_g": 40, "fat_g": 7,
     "timing": "7:30 AM - 9:00 AM", "allergens": ["peanuts"]},
    {"menu_type": "hostel_mess", "meal_type": "breakfast", "name": "Idli Sambar", "category": "veg",
     "calories": 280, "protein_g": 8, "carbs_g": 45, "fat_g": 4,
     "timing": "7:30 AM - 9:00 AM", "allergens": []},
    {"menu_type": "hostel_mess", "meal_type": "breakfast", "name": "Bread Butter Jam", "category": "veg",
     "calories": 220, "protein_g": 5, "carbs_g": 30, "fat_g": 9,
     "timing": "7:30 AM - 9:00 AM", "allergens": ["gluten", "dairy"]},
    {"menu_type": "hostel_mess", "meal_type": "breakfast", "name": "Boiled Eggs (2)", "category": "non_veg",
     "calories": 155, "protein_g": 13, "carbs_g": 1, "fat_g": 11,
     "timing": "7:30 AM - 9:00 AM", "allergens": ["eggs"]},
    {"menu_type": "hostel_mess", "meal_type": "lunch", "name": "Rice + Dal + Sabzi", "category": "veg",
     "calories": 450, "protein_g": 14, "carbs_g": 70, "fat_g": 10,
     "timing": "12:30 PM - 2:00 PM", "allergens": []},
    {"menu_type": "hostel_mess", "meal_type": "lunch", "name": "Roti (3) + Rajma", "category": "veg",
     "calories": 480, "protein_g": 16, "carbs_g": 75, "fat_g": 9,
     "timing": "12:30 PM - 2:00 PM", "allergens": ["gluten"]},
    {"menu_type": "hostel_mess", "meal_type": "lunch", "name": "Curd Rice", "category": "veg",
     "calories": 380, "protein_g": 10, "carbs_g": 60, "fat_g": 9,
     "timing": "12:30 PM - 2:00 PM", "allergens": ["dairy"]},
    {"menu_type": "hostel_mess", "meal_type": "lunch", "name": "Chicken Curry + Rice", "category": "non_veg",
     "calories": 550, "protein_g": 30, "carbs_g": 60, "fat_g": 18,
     "timing": "12:30 PM - 2:00 PM", "allergens": []},
    {"menu_type": "hostel_mess", "meal_type": "snacks", "name": "Tea + Biscuits", "category": "beverages",
     "calories": 150, "protein_g": 2, "carbs_g": 22, "fat_g": 6,
     "timing": "4:30 PM - 5:30 PM", "allergens": ["gluten", "dairy"]},
    {"menu_type": "hostel_mess", "meal_type": "snacks", "name": "Samosa (2 pcs)", "category": "snacks",
     "calories": 320, "protein_g": 6, "carbs_g": 35, "fat_g": 17,
     "timing": "4:30 PM - 5:30 PM", "allergens": ["gluten"]},
    {"menu_type": "hostel_mess", "meal_type": "dinner", "name": "Roti + Paneer + Dal", "category": "veg",
     "calories": 520, "protein_g": 22, "carbs_g": 60, "fat_g": 18,
     "timing": "7:30 PM - 9:00 PM", "allergens": ["gluten", "dairy"]},
    {"menu_type": "hostel_mess", "meal_type": "dinner", "name": "Rice + Sambar + Rasam", "category": "veg",
     "calories": 420, "protein_g": 12, "carbs_g": 70, "fat_g": 8,
     "timing": "7:30 PM - 9:00 PM", "allergens": []},
    {"menu_type": "hostel_mess", "meal_type": "dinner", "name": "Egg Bhurji + Roti", "category": "non_veg",
     "calories": 450, "protein_g": 20, "carbs_g": 45, "fat_g": 18,
     "timing": "7:30 PM - 9:00 PM", "allergens": ["gluten", "eggs"]},
]

# College Canteen Menu
CANTEEN = [
    {"menu_type": "college_canteen", "meal_type": "breakfast", "name": "Veg Sandwich", "category": "veg",
     "calories": 240, "protein_g": 8, "carbs_g": 32, "fat_g": 9, "price": 45,
     "timing": "8:00 AM - 11:00 AM", "allergens": ["gluten"]},
    {"menu_type": "college_canteen", "meal_type": "breakfast", "name": "Masala Dosa", "category": "veg",
     "calories": 320, "protein_g": 7, "carbs_g": 48, "fat_g": 11, "price": 60,
     "timing": "8:00 AM - 11:00 AM", "allergens": []},
    {"menu_type": "college_canteen", "meal_type": "lunch", "name": "Veg Thali", "category": "veg",
     "calories": 550, "protein_g": 16, "carbs_g": 80, "fat_g": 15, "price": 90,
     "timing": "12:00 PM - 3:00 PM", "allergens": []},
    {"menu_type": "college_canteen", "meal_type": "lunch", "name": "Paneer Sandwich", "category": "veg",
     "calories": 380, "protein_g": 18, "carbs_g": 35, "fat_g": 18, "price": 70,
     "timing": "12:00 PM - 3:00 PM", "allergens": ["gluten", "dairy"]},
    {"menu_type": "college_canteen", "meal_type": "lunch", "name": "Chicken Sandwich", "category": "non_veg",
     "calories": 420, "protein_g": 25, "carbs_g": 35, "fat_g": 20, "price": 90,
     "timing": "12:00 PM - 3:00 PM", "allergens": ["gluten"]},
    {"menu_type": "college_canteen", "meal_type": "snacks", "name": "Fruit Chat", "category": "veg",
     "calories": 120, "protein_g": 2, "carbs_g": 28, "fat_g": 1, "price": 40,
     "timing": "All day", "allergens": []},
    {"menu_type": "college_canteen", "meal_type": "snacks", "name": "Buttermilk", "category": "beverages",
     "calories": 60, "protein_g": 3, "carbs_g": 6, "fat_g": 2, "price": 20,
     "timing": "All day", "allergens": ["dairy"]},
    {"menu_type": "college_canteen", "meal_type": "snacks", "name": "Roasted Chana", "category": "snacks",
     "calories": 110, "protein_g": 6, "carbs_g": 18, "fat_g": 2, "price": 25,
     "timing": "All day", "allergens": []},
    {"menu_type": "college_canteen", "meal_type": "snacks", "name": "Fresh Lime Soda", "category": "beverages",
     "calories": 80, "protein_g": 0, "carbs_g": 20, "fat_g": 0, "price": 30,
     "timing": "All day", "allergens": []},
    {"menu_type": "college_canteen", "meal_type": "dinner", "name": "Pav Bhaji", "category": "veg",
     "calories": 480, "protein_g": 12, "carbs_g": 65, "fat_g": 18, "price": 80,
     "timing": "6:00 PM - 8:00 PM", "allergens": ["gluten"]},
    {"menu_type": "college_canteen", "meal_type": "dinner", "name": "Veg noodles", "category": "veg",
     "calories": 420, "protein_g": 10, "carbs_g": 60, "fat_g": 15, "price": 70,
     "timing": "6:00 PM - 8:00 PM", "allergens": ["gluten", "soy"]},
]


async def seed():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        for u in USERS:
            session.add(User(
                name=u["name"], email=u["email"],
                password_hash=pwd_context.hash(u["password"]),
                student_type=u["student_type"],
                age=u["age"], weight=u["weight"], height=u["height"],
                body_type=u["body_type"], fitness_level=u["fitness_level"],
                activity_level=u["activity_level"], fitness_goal=u["fitness_goal"],
                dietary_preference=u["dietary_preference"], allergies=u["allergies"],
                points=u["points"], current_streak=u["current_streak"],
                longest_streak=u["longest_streak"],
                last_activity_date=date.today().isoformat(),
                created_at=datetime.utcnow(),
            ))
        await session.commit()

        # Demo activities
        from sqlalchemy import select as sa_select
        demo = (await session.execute(
            sa_select(User).where(User.email == "demo@fitcampus.com")
        )).scalar_one()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        for a in [
            {"activity_type": "walking", "duration_minutes": 30, "calories_estimate": 130,
             "status": "completed", "date": yesterday, "points_earned": 15},
            {"activity_type": "stretching", "duration_minutes": 10, "calories_estimate": 30,
             "status": "completed", "date": yesterday, "points_earned": 5},
        ]:
            session.add(Activity(user_id=demo.id, **a, created_at=datetime.utcnow()))

        for c in CHALLENGES:
            session.add(Challenge(**c))

        # Menu items
        for item in HOSTEL_MESS + CANTEEN:
            session.add(MenuItem(**item))

        await session.commit()

    await engine.dispose()
    print("✅ Seeded", len(USERS), "users,", len(CHALLENGES), "challenges, and",
          len(HOSTEL_MESS) + len(CANTEEN), "menu items.")
    print("Demo login: demo@fitcampus.com / demo1234 (Day Scholar)")
    print("Hosteler login: aarav@fitcampus.com / demo1234")
    print("Vegan user: ananya@fitcampus.com / demo1234 (allergic to dairy)")


if __name__ == "__main__":
    asyncio.run(seed())