import asyncio
from bot import bot, dp  # Импортируем бот и диспетчер
from handlers import router
from database.models import async_main


async def main():
    await async_main()
    dp.include_router(router)
    await dp.start_polling(bot)  # Запускаем бота

if __name__ == "__main__":
    asyncio.run(main())
