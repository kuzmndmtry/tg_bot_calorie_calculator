from enum import Enum as PyEnum
from datetime import date
from typing import List, Optional
from sqlalchemy import Column, Date, Integer, String, func, select
from datetime import date
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from config import DB_URL

class Base(DeclarativeBase):
    pass

class Profile(Base):
   __tablename__ = 'profiles'
   user_id: Mapped[int] = mapped_column(primary_key=True)
   weight: Mapped[float] = mapped_column(nullable=False)
   height: Mapped[float] = mapped_column(nullable=False)
   age: Mapped[int] = mapped_column(nullable=False)
   activity: Mapped[int] = mapped_column(nullable=False)
   city: Mapped[str] = mapped_column(String(100), nullable=False)
   calories_goal: Mapped[int] = mapped_column(nullable=False)
   water_goal: Mapped[float] = mapped_column(nullable=False)

# Создаём асинхронный движок и сессии
engine = create_async_engine(DB_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Функция для создания таблиц
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Сохраняем профиль
async def save_profile(user_id: int, data: dict):
    async with async_session() as session:
        async with session.begin():
            profile = await session.get(Profile, user_id)
            if not profile:
                profile = Profile(user_id=user_id)
            profile.weight = float(data["weight"])
            profile.height = float(data["height"])
            profile.age = int(data["age"])
            profile.activity = int(data["activity"])
            profile.city = data["city"]
            profile.calories_goal = data.get("calories_goal")
            profile.water_goal = data.get("water_goal")
            session.add(profile)
        await session.commit()

# Получаем профиль
async def get_profile(user_id: int):
    async with async_session() as session:
        profile = await session.get(Profile, user_id)
        return profile


class Water_Log(Base):
   __tablename__ = 'water_logs'
   id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
   user_id: Mapped[int] = mapped_column(nullable=False)
   amount: Mapped[int] = mapped_column(nullable=False)
   date: Mapped[date] = mapped_column(Date, nullable=False)

# сохраняем воду
async def save_water(user_id: int, amount: int):
    async with async_session() as session:
        async with session.begin():
            water_log = Water_Log (
                user_id = user_id, 
                amount = amount,
                date = date.today()
            )
            session.add(water_log)
        await session.commit()

# считаем воду
async def amount_of_water_per_day(user_id: int):
    async with async_session() as session:
        amount_of_water = select(func.sum(Water_Log.amount)).where(
            Water_Log.user_id == user_id,
            Water_Log.date == date.today()
            )
        result = await session.execute(amount_of_water)
        amount = result.scalar()
        return amount

class  Food_Log(Base):
   __tablename__ = 'food_logs'
   id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
   user_id: Mapped[int] = mapped_column(nullable=False)
   name: Mapped[str] = mapped_column(String(100),nullable=False)
   ccals: Mapped[float] = mapped_column(nullable=False)
   date: Mapped[date] = mapped_column(Date, nullable=False)

# сохраняем еду 
async def save_food(user_id: int,  name: str, ccals: float):
    async with async_session() as session:
        async with session.begin():
            food_log = Food_Log (
                user_id = user_id, 
                ccals = ccals,
                name = name,
                date = date.today()
            )
            session.add(food_log)
        await session.commit()

# считаем еду
async def amount_of_food_per_day(user_id: int):
    async with async_session() as session:
        amount_of_food = select(func.sum(Food_Log.ccals)).where(
            Food_Log.user_id == user_id,
            Food_Log.date == date.today()
            )
        result = await session.execute(amount_of_food)
        amount = result.scalar()
        return amount
    

class Workout_log(Base):
    __tablename__ = 'workout_log'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100),nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

# сохраняем трен 
async def save_workout(user_id: int,  name: str, amount: float):
    async with async_session() as session:
        async with session.begin():
            workout_log = Workout_log (
                user_id = user_id, 
                amount = amount,
                name = name,
                date = date.today()
            )
            session.add(workout_log)
        await session.commit()

# считаем трен
async def amount_of_workout_per_day(user_id: int):
    async with async_session() as session:
        amount_of_workout = select(func.sum(Workout_log.amount)).where(
            Workout_log.user_id == user_id,
            Workout_log.date == date.today()
            )
        result = await session.execute(amount_of_workout)
        amount = result.scalar()
        return amount


