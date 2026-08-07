from app.models import Lot, Analysis
from app.config import Config

class Strategy:
    @staticmethod
    def check_lot(lot: Lot) -> bool:
        # Базовые фильтры по коллекции, цене
        if lot.collection in Config.BLACKLIST_COLLECTIONS:
            return False
        if lot.price > Config.BUDGET_LIMIT:
            return False
        return True

    @staticmethod
    def check_analysis(analysis: Analysis) -> bool:
        # Можно добавить дополнительные проверки на основе анализа
        return True
