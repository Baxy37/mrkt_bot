import asyncio
import sys
from aiogram import Bot, Dispatcher
from app.config import Config
from app.logger import logger
from app.database import Database
from app.analyzer import Analyzer
from app.strategy import Strategy
from app.scanner import Scanner
from app.notifier import Notifier
from app.bot_handlers import router, setup_handlers

async def main():
    # Проверка наличия токена
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN не задан в .env")
        sys.exit(1)

    # Инициализация БД
    db = Database()
    await db.init()
    logger.info("Database initialized")

    # Инициализация стратегии и анализатора
    strategy = Strategy()
    analyzer = Analyzer(strategy)

    # Инициализация сканера
    scanner = Scanner(db, analyzer)

    # Инициализация бота и диспетчера
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher()

    # Инициализация нотификатора
    notifier = Notifier(bot, db)

    # Передаём зависимости в хендлеры
    setup_handlers(db, notifier, scanner)
    dp.include_router(router)

    # Запускаем сканер (если не приостановлен)
    # Здесь можно проверить настройки пользователя, но для простоты запускаем сразу
    scanner.start()

    # Запускаем поллинг
    try:
        logger.info("Bot started polling")
        await dp.start_polling(bot)
    finally:
        scanner.stop()
        await db.close()
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
