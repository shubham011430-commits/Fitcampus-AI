from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Date, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()


class StudentType(str, enum.Enum):
    HOSTELER = "hosteler"
    DAY_SCHOLAR = "day_scholar"


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    SNACKS = "snacks"
    DINNER = "dinner"


class MenuCategory(str, enum.Enum):
    VEG = "veg"
    NON_VEG = "non_veg"
    VEGAN = "vegan"
    BEVERAGES = "beverages"
    SNACKS = "snacks"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    student_type = Column(String(20), default="day_scholar")  # hosteler / day_scholar
    age = Column(Integer)
    weight = Column(Float)
    height = Column(Float)
    body_type = Column(String(50))
    fitness_level = Column(String(50), default="beginner")
    activity_level = Column(String(50), default="low")
    fitness_goal = Column(String(50), default="general_wellness")
    dietary_preference = Column(String(50), default="veg")  # veg / non_veg / vegan / eggetarian
    allergies = Column(JSON, default=list)  # ["peanuts", "dairy", ...]
    points = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    activities = relationship("Activity", back_populates="user")
    activity_sessions = relationship("ActivitySession", back_populates="user")
    exercises = relationship("Exercise", back_populates="user")
    journeys = relationship("Journey", back_populates="user")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    calories_estimate = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    date = Column(String(20), nullable=False, index=True)
    points_earned = Column(Integer, default=0)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activities")


class ActivitySession(Base):
    """Tracks live activity sessions with start/stop workflow."""
    __tablename__ = "activity_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer, default=0)
    steps_count = Column(Integer, default=0)
    distance_km = Column(Float, default=0)
    calories_estimate = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active / completed / cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activity_sessions")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exercise_name = Column(String(100), nullable=False)
    repetitions = Column(Integer, default=0)
    duration = Column(Integer, default=0)
    form_score = Column(Float, default=0)
    detection_method = Column(String(20), default="manual")  # camera / manual
    points_earned = Column(Integer, default=0)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="exercises")


class Journey(Base):
    __tablename__ = "journeys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mode = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    start_location = Column(String(200))
    start_lat = Column(Float)
    start_lng = Column(Float)
    end_time = Column(DateTime)
    end_location = Column(String(200))
    end_lat = Column(Float)
    end_lng = Column(Float)
    distance_km = Column(Float, default=0)
    duration_minutes = Column(Integer, default=0)
    calories_burned = Column(Integer, default=0)
    steps_estimate = Column(Integer, default=0)
    status = Column(String(20), default="ongoing")
    points_earned = Column(Integer, default=0)
    date = Column(String(20), nullable=False, index=True)

    user = relationship("User", back_populates="journeys")


class MenuItem(Base):
    """Hostel mess or college canteen menu items."""
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    menu_type = Column(String(20), nullable=False, index=True)  # 'hostel_mess' or 'college_canteen'
    meal_type = Column(String(20), nullable=False)  # breakfast/lunch/snacks/dinner
    name = Column(String(200), nullable=False)
    category = Column(String(50), default="veg")  # veg/non_veg/vegan/beverages/snacks
    description = Column(Text)
    calories = Column(Integer)
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fat_g = Column(Float)
    price = Column(Float)  # for canteen items
    available = Column(Boolean, default=True)
    timing = Column(String(100))  # e.g., "7:30 AM - 9:00 AM"
    allergens = Column(JSON, default=list)  # ["nuts", "dairy", "gluten"]
    created_at = Column(DateTime, default=datetime.utcnow)


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    start_date = Column(String(20))
    end_date = Column(String(20))
    reward_points = Column(Integer, default=0)
    participants = Column(Integer, default=0)


class ChallengeProgress(Base):
    __tablename__ = "challenge_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class DietRecommendation(Base):
    __tablename__ = "diet_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_snapshot = Column(JSON)
    recommendations = Column(JSON)
    source = Column(String(20), default="rule_based")  # gemini / rule_based
    generated_at = Column(DateTime, default=datetime.utcnow)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class FormSnapshot(Base):
    __tablename__ = "form_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exercise = Column(String(50))
    angles = Column(JSON)
    phase = Column(String(20))
    rep_count = Column(Integer, default=0)
    form_score = Column(Float, default=0)
    confidence = Column(Float, default=0)
    feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)