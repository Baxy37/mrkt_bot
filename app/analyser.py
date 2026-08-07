from typing import Optional
from app.models import Lot, Analysis, Deal
from app.config import Config
from app.strategy import Strategy
from app.logger import logger
import random

class Analyzer:
    def __init__(self, strategy: Strategy):
        self.strategy = strategy

    async def analyze(self, lot: Lot) -> Deal:
        # Применяем фильтры из стратегии
        if not self.strategy.check_lot(lot):
            return Deal(lot=lot, analysis=None, is_valid=False)

        # Симуляция расчётов (замените на реальную логику)
        # Предположим, что ориентир рыночной цены берём из внешнего источника или вычисляем
        market_price = lot.price * (1 + random.uniform(0.1, 0.5))  # имитация
        spread = (market_price - lot.price) / lot.price * 100
        # Комиссии: предположим 5%
        fee = lot.price * 0.05
        profit = market_price - lot.price - fee
        # Ликвидность: случайно
        liquidity = random.uniform(30, 95)
        # Риск: обратно пропорционален ликвидности
        risk = 100 - liquidity + random.uniform(-10, 10)
        risk = max(0, min(100, risk))
        # Рейтинг: комбинация прибыли и ликвидности
        rating = (profit / lot.price * 100) * 0.4 + liquidity * 0.6
        rating = max(0, min(100, rating))

        analysis = Analysis(
            profit=profit,
            spread=spread,
            liquidity=liquidity,
            rating=rating,
            risk=risk,
            optimal_price=market_price * 0.95,
            fast_price=market_price * 0.85
        )

        # Проверяем пороги
        is_valid = (
            profit >= Config.MIN_PROFIT and
            rating >= Config.MIN_RATING and
            lot.price <= Config.BUDGET_LIMIT and
            lot.collection not in Config.BLACKLIST_COLLECTIONS
        )

        # Дополнительно проверка стратегии (можно переопределить)
        is_valid = is_valid and self.strategy.check_analysis(analysis)

        return Deal(lot=lot, analysis=analysis, is_valid=is_valid)
