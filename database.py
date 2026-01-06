from enum import Enum as PyEnum
from datetime import date
from typing import List, Optional
from sqlalchemy import Column, Integer, String
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
   date: Mapped[date] = mapped_column(nullable=False)

# Сохраняем воду
async def save_profile(user_id: int, amount: int):
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




