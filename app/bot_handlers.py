from aiogram import Router, types
from aiogram.filters import Command
from app.database import Database
from app.notifier import Notifier
from app.scanner import Scanner
from app.logger import logger
from app.config import Config

router = Router()

# Глобальные зависимости (будут установлены в main)
db: Database = None
notifier: Notifier = None
scanner: Scanner = None

def setup_handlers(_db, _notifier, _scanner):
    global db, notifier, scanner
    db = _db
    notifier = _notifier
    scanner = _scanner

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    await db.create_user(user_id)
    await message.answer(
        "👋 Привет! Я бот-аналитик MRKT.\n"
        "Я мониторю лоты и присылаю уведомления о выгодных сделках.\n"
        "Команды:\n"
        "/status — текущий статус\n"
        "/stats — статистика\n"
        "/settings — настройки\n"
        "/pause — пауза\n"
        "/resume — возобновить\n"
        "/help — помощь"
    )

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await db.create_user(user_id)
        user = await db.get_user(user_id)
    mode = user["mode"]
    paused = user["paused"]
    status_text = (
        f"📊 <b>Статус</b>\n"
        f"Режим: {mode}\n"
        f"Мониторинг: {'⏸ приостановлен' if paused else '▶ активен'}\n"
        f"Минимальный рейтинг: {user['min_rating']}\n"
        f"Бюджет: ${user['budget_limit']}\n"
        f"Чёрный список: {', '.join(user['blacklist']) or 'нет'}"
    )
    await message.answer(status_text, parse_mode="HTML")

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    # Простая статистика за день
    rows = await db.get_stats(days=1)
    if rows:
        row = rows[0]  # последний день
        total = row[1]
        avg_profit = row[2]
        avg_rating = row[3]
        total_profit = row[4]
        text = f"📈 <b>Статистика за сегодня</b>\nЛотов: {total}\nСредняя прибыль: ${avg_profit:.2f}\nСредний рейтинг: {avg_rating:.1f}\nОбщая прибыль: ${total_profit:.2f}"
    else:
        text = "Нет данных за сегодня"
    await message.answer(text, parse_mode="HTML")

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    # Упрощённо: выводим текущие настройки и предлагаем изменить через команды (можно реализовать инлайн-клавиатуру)
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await db.create_user(user_id)
        user = await db.get_user(user_id)
    text = (
        f"⚙️ <b>Настройки</b>\n"
        f"Режим: {user['mode']} (изменить: /setmode test|analytics|semiauto)\n"
        f"Мин. рейтинг: {user['min_rating']} (изменить: /setrating <число>)\n"
        f"Бюджет: ${user['budget_limit']} (изменить: /setbudget <сумма>)\n"
        f"Чёрный список: {', '.join(user['blacklist']) or 'нет'} (изменить: /setblacklist кол1,кол2)"
    )
    await message.answer(text, parse_mode="HTML")

# Дополнительные команды для изменения настроек (можно расширить)
@router.message(Command("pause"))
async def cmd_pause(message: types.Message):
    user_id = message.from_user.id
    await db.update_user(user_id, paused=1)
    await message.answer("⏸ Мониторинг приостановлен.")

@router.message(Command("resume"))
async def cmd_resume(message: types.Message):
    user_id = message.from_user.id
    await db.update_user(user_id, paused=0)
    await message.answer("▶ Мониторинг возобновлён.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 <b>Помощь</b>\n"
        "Я анализирую лоты MRKT и отправляю уведомления.\n"
        "Команды: /start, /status, /stats, /settings, /pause, /resume, /help\n"
        "В полуавтоматическом режиме на уведомлениях есть кнопки для подтверждения.\n"
        "Все настройки хранятся в БД, можно менять без перезапуска.",
        parse_mode="HTML"
    )

# Обработчик callback-кнопок (полуавтомат)
@router.callback_query(lambda c: c.data and c.data.startswith(("buy_", "skip_")))
async def handle_buy_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    action, lot_id = callback.data.split("_")
    if action == "buy":
        # В реальности здесь можно вызвать API покупки, но мы только логируем
        await db.mark_confirmed(lot_id)
        await callback.message.edit_text(callback.message.text + "\n\n✅ Вы подтвердили покупку! (симуляция)")
        await callback.answer("Покупка подтверждена")
        logger.info(f"User {user_id} confirmed purchase of lot {lot_id}")
    else:
        await callback.message.edit_text(callback.message.text + "\n\n❌ Пропущено")
        await callback.answer("Пропущено")
