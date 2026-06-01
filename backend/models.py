from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supabase_user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[float] = mapped_column(Float)
    height_cm: Mapped[float] = mapped_column(Float)
    goal: Mapped[str] = mapped_column(String(200))
    dietary_restrictions: Mapped[str] = mapped_column(String(300), default="")
    fitness_level: Mapped[str] = mapped_column(String(50))
    sex: Mapped[str] = mapped_column(String(10), default="masculino")
    available_equipment: Mapped[str] = mapped_column(String(300), default="")

    diet_plans: Mapped[list["DietPlan"]] = relationship(back_populates="user")
    workout_plans: Mapped[list["WorkoutPlan"]] = relationship(back_populates="user")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "age": self.age,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "goal": self.goal,
            "dietary_restrictions": self.dietary_restrictions,
            "fitness_level": self.fitness_level,
            "sex": self.sex,
            "available_equipment": self.available_equipment,
        }

class DietPlan(Base):
    __tablename__ = "diet_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    content: Mapped[str] = mapped_column(Text)
    calories_target: Mapped[int] = mapped_column(Integer)

    user: Mapped["UserProfile"] = relationship(back_populates="diet_plans")

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    content: Mapped[str] = mapped_column(Text)
    focus: Mapped[str] = mapped_column(String(100))

    user: Mapped["UserProfile"] = relationship(back_populates="workout_plans")
