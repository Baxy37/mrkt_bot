from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class Lot(BaseModel):
    id: str
    name: str
    collection: str
    price: float          # цена в USD (приводим к единой валюте)
    currency: str = "USD"
    url: str
    image: Optional[str] = None
    created_at: datetime
    extra: Dict[str, Any] = {}

class Analysis(BaseModel):
    profit: float          # ожидаемая чистая прибыль
    spread: float          # спред в процентах
    liquidity: float       # 0-100, на основе истории продаж
    rating: float          # 0-100, итоговый рейтинг сделки
    risk: float            # 0-100, риск
    optimal_price: float   # оптимальная цена для перепродажи
    fast_price: float      # быстрая цена (ниже для быстрой продажи)

class Deal(BaseModel):
    lot: Lot
    analysis: Analysis
    is_valid: bool         # прошло ли фильтры
    notified: bool = False
    user_confirmed: bool = False
