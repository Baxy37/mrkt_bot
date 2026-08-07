import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import aiohttp
from app.config import Config
from app.logger import logger
from app.models import Lot
from app.analyzer import Analyzer
from app.database import Database

class Scanner:
    def __init__(self, db: Database, analyzer: Analyzer):
        self.db = db
        self.analyzer = analyzer
        self.last_seen_ids = set()
        self.running = False
        self.task = None

    async def _fetch_lots_from_api(self) -> List[Dict[str, Any]]:
        """Адаптер для MRKT. Здесь имитация, замените на реальный запрос."""
        # В реальности: async with aiohttp.ClientSession() as session:
        #     resp = await session.get(Config.MRKT_API_URL, params={"limit": 50})
        #     data = await resp.json()
        #     return data.get("lots", [])
        # Для демонстрации генерируем случайные лоты
        collections = ["Art", "CryptoPunks", "BoredApe", "Doodles", "Azuki"]
        lots = []
        for i in range(random.randint(1, 5)):
            lot = {
                "id": f"lot_{datetime.utcnow().timestamp()}_{i}",
                "name": f"Item {i}",
                "collection": random.choice(collections),
                "price": round(random.uniform(10, 2000), 2),
                "currency": "USD",
                "url": f"https://mrkt.io/lot/{i}",
                "image": None,
                "created_at": datetime.utcnow().isoformat()
            }
            lots.append(lot)
        return lots

    async def _process_new_lots(self, lots: List[Dict]):
        for lot_data in lots:
            lot_id = lot_data["id"]
            if lot_id in self.last_seen_ids:
                continue
            self.last_seen_ids.add(lot_id)
            # Проверяем, не обработан ли уже
            existing = await self.db.get_lot(lot_id)
            if existing:
                continue

            # Преобразуем в Lot
            lot = Lot(**lot_data)
            # Анализируем
            deal = await self.analyzer.analyze(lot)
            if deal.is_valid:
                # Сохраняем в БД
                await self.db.save_lot(lot.dict(), deal.analysis.dict())
                # Передаём в notifier через бота (через событие или callback)
                # Будем использовать глобальный обработчик, установленный в main
                from app.notifier import Notifier
                notifier = Notifier()
                await notifier.send_deal_notification(deal)
            else:
                # Логируем, но не сохраняем (или сохраняем с пометкой invalid)
                logger.info(f"Lot {lot_id} skipped: not valid")

    async def scan_once(self):
        try:
            logger.info("Scanning MRKT for new lots...")
            lots = await self._fetch_lots_from_api()
            if lots:
                await self._process_new_lots(lots)
            else:
                logger.debug("No lots received")
        except Exception as e:
            logger.error(f"Scan error: {e}", exc_info=True)

    async def continuous_scan(self):
        """Запускается в отдельной задаче"""
        self.running = True
        while self.running:
            if not self.running:
                break
            await self.scan_once()
            await asyncio.sleep(Config.SCAN_INTERVAL)

    def start(self):
        if self.task is None or self.task.done():
            self.running = True
            self.task = asyncio.create_task(self.continuous_scan())
            logger.info("Scanner started")

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            logger.info("Scanner stopped")
