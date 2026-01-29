from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from xync_schema.enums import AdStatus, OrderStatus
from xync_schema import models


class CurEx(BaseModel):
    exid: int | str
    ticker: str
    scale: int = None
    rate: float | None = None
    minimum: float | None = None


class CoinEx(CurEx):
    p2p: bool = None


class PmExBank(BaseModel):
    # id: int | None = None
    exid: str
    name: str


class BaseAd(BaseModel):
    amount: int
    auto_msg: str | None
    created_at: int  # utc(0) seconds
    exid: int
    id: int = None
    max_fiat: int
    min_fiat: int
    premium: int
    price: int
    quantity: int | None = None
    status: Literal[AdStatus.active, AdStatus.defActive, AdStatus.soldOut]  # 10: online; 20: offline; 30: completed

    cond_id: int | None = None
    maker_id: int
    pair_side_id: int

    pms: list[models.Pm]

    _unq = "exid", "maker_id"

    class Config:
        arbitrary_types_allowed = True


class AdBuy(BaseAd):
    pmexs_: list[models.PmEx]


class AdSale(BaseAd):
    credexs_: list[models.CredEx]


class BaseOrder(BaseModel):
    exid: int  #
    amount: float
    quantity: float
    ad_id: int
    cred_id: int
    taker_id: int
    status: OrderStatus = OrderStatus.created
    created_at: datetime

    _unq = "id", "exid", "ad_id", "taker_id"


class OrderIn(BaseModel):
    exid: int
    amount: float
    created_at: datetime
    ad: models.Ad
    cred: models.Cred
    taker: models.Actor
    id: int = None
    maker_topic: int | None = None
    taker_topic: int | None = None
    status: OrderStatus = OrderStatus.created
    _unq = "id", "exid", "amount", "maker_topic", "taker_topic", "ad", "cred", "taker"

    class Config:
        arbitrary_types_allowed = True
