import asyncio
import random
from enum import unique
from functools import partial
from discord.ui import View, Button
from discord import ButtonStyle
from sqlalchemy import Column, Integer, String, ForeignKey, select, insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import func

DATABASE_URL = "sqlite+aiosqlite:///words.db"

Base = declarative_base()
engine = None


# Модели
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    score = Column(Integer, default=0)


class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    word_ru = Column(String(100))
    word_en = Column(String(100))


# Инициализация БД
async def init_db():
    global engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


async def get_session():
    if engine is None:
        await init_db()
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return async_session()


# Функции для бота
async def add_word(user_id: int, word_ru: str, word_en: str):
    async with await get_session() as session:
        # Добавляем пользователя, если его нет
        existing = await session.execute(select(User).where(User.id == user_id))
        if not existing.scalar_one_or_none():
            session.add(User(id=user_id))
            await session.flush()

        # Добавляем слово
        session.add(Word(user_id=user_id, word_ru=word_ru, word_en=word_en))
        await session.commit()


from sqlalchemy import func, select  # func нужно добавить в импорт


async def get_random_word(user_id: int):
    async with await get_session() as session:
        result = await session.execute(
            select(Word.word_ru, Word.word_en)
            .where(Word.user_id == user_id)
            .order_by(func.random())
            .limit(1)
        )
        row = result.first()

        if row is None:
            return None
        return row.word_ru, row.word_en

async def update_score(user_id: int, points: int = 1):
    async with await get_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user_obj = user.scalar_one_or_none()
        if user_obj:
            user_obj.score += points
        else:
            session.add(User(id=user_id, score=points))
        await session.commit()


async def get_stats(user_id: int):
    async with await get_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user_obj = user.scalar_one_or_none()
        if user_obj:
            # Подсчитываем количество слов
            words_result = await session.execute(
                select(Word).where(Word.user_id == user_id)
            )
            words_count = len(words_result.scalars().all())
            return user_obj.score, words_count
        return 0, 0


async def get_random_wrong_translations(user_id: int, correct_word_en: str, count: int = 3):
    async with await get_session() as session:
        result = await session.execute(
            select(Word.word_en)  # только английские переводы
            .where(
                Word.user_id == user_id,
                Word.word_en != correct_word_en
            )
            .order_by(func.random())
            .limit(count * 2)
        )
        all_wrong = result.scalars().all()
        unique_wrong = list(set(all_wrong))

        if len(unique_wrong) < count:
            return unique_wrong  # если меньше 3, возвращаем сколько есть

        return random.sample(unique_wrong, count)

async def create_translation_quiz(user_id: int):
    correct_pair = await get_random_word(user_id)
    if not correct_pair:
        return None

    word_ru, correct_word_en = correct_pair
    wrong_translations = await get_random_wrong_translations(user_id, correct_word_en, 3)

    options = [correct_word_en] + wrong_translations
    random.shuffle(options)

    view = View(timeout=30)

    async def quiz_callback(interaction, selected_option):
        if selected_option == correct_word_en:
            await interaction.response.send_message("✅ Правильно! Молодец!", ephemeral=True)
            await update_score(user_id, 1)
        else:
            await interaction.response.send_message(f"❌ Неправильно. Правильный ответ: {correct_word_en}", ephemeral=True)
        view.stop()  # останавливаем View после ответа

    for option in options:
        button = Button(label=option, style=ButtonStyle.primary)
        button.callback = partial(quiz_callback, selected_option=option)
        view.add_item(button)

    return {
        'question': f"Как переводится слово **«{word_ru}»**?",
        'view': view,
        'correct_answer': correct_word_en
    }
async def get_leaderboard(limit: int = 5):
    async with await get_session() as session:
        result = await session.execute(
            select(User).order_by(User.score.desc()).limit(limit)
        )
        return result.scalars().all()

async def get_leaderboard(limit: int = 5):
    async with await get_session() as session:
        result = await session.execute(
            select(User).order_by(User.score.desc()).limit(limit)
        )
        return result.scalars().all()