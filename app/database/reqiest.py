from awesome_project.app.database.models import async_session
from awesome_project.app.database.models import User
from sqlalchemy import select, update


async def get_user_by_tg_id(tg_id):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        return user


async def commit_user(start_time, tg_id):
    async with async_session() as session:
        user = await get_user_by_tg_id(tg_id)
        if user:
            user.time = start_time.isoformat()
            user.days_survival = "0"
        else:
            user = User(tg_id=tg_id, time=start_time.isoformat(), days_survival="0")
            session.add(user)
        await session.commit()


async def increment_days(tg_id: int):
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.tg_id == tg_id)
            .values(days_survival=User.days_survival + 1)
        )
        await session.commit()


async def rat_deaf(tg_id):
    async with async_session() as session:
        stmt = (
            update(User)
            .where(User.tg_id == tg_id)
            .values(days_survival="0")
        )
        await session.execute(stmt)
        await session.commit()


async def get_days(tg_id):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalars().first()
        if not user or user.days_survival is None:
            return 0
        try:
            return int(user.days_survival)
        except ValueError:
            # На всякий случай, если в базе хранится нечисловая строка
            return 0