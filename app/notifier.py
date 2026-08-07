from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.models import Deal
from app.config import Config
from app.logger import logger
from app.database import Database

class Notifier:
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db
        self.last_notified = {}  # для защиты от спама по ID

    async def send_deal_notification(self, deal: Deal, user_id: int):
        if deal.lot.id in self.last_notified:
            return  # уже уведомляли
        self.last_notified[deal.lot.id] = True

        # Формируем сообщение
        msg = (
            f"🔔 <b>Новая сделка!</b>\n"
            f"<b>Название:</b> {deal.lot.name}\n"
            f"<b>Коллекция:</b> {deal.lot.collection}\n"
            f"<b>Цена:</b> ${deal.lot.price:.2f}\n"
            f"<b>Ориентир:</b> ${deal.analysis.optimal_price:.2f}\n"
            f"<b>Прибыль:</b> ${deal.analysis.profit:.2f}\n"
            f"<b>Рейтинг:</b> {deal.analysis.rating:.1f}/100\n"
            f"<b>Риск:</b> {deal.analysis.risk:.1f}/100\n"
            f"<b>Ликвидность:</b> {deal.analysis.liquidity:.1f}/100\n"
            f"<a href='{deal.lot.url}'>Открыть лот</a>"
        )

        # Кнопки для полуавтоматического режима
        kb = None
        user_settings = await self.db.get_user(user_id)
        mode = user_settings["mode"] if user_settings else Config.MODE
        if mode == "semiauto":
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Купить", callback_data=f"buy_{deal.lot.id}"),
                    InlineKeyboardButton(text="❌ Пропустить", callback_data=f"skip_{deal.lot.id}")
                ]
            ])

        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=msg,
                reply_markup=kb,
                parse_mode="HTML"
            )
            await self.db.mark_notified(deal.lot.id)
            logger.info(f"Notification sent for lot {deal.lot.id} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    async def send_status_message(self, user_id: int, status: str):
        await self.bot.send_message(chat_id=user_id, text=status, parse_mode="HTML")
