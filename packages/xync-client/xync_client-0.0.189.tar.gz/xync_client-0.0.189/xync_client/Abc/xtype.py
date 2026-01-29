import re
from typing import Literal, ClassVar

from pydantic import BaseModel, model_validator, model_serializer, Field
from pydantic_core.core_schema import SerializationInfo
from tortoise.expressions import Q
from tortoise.functions import Count
from x_model.func import ArrayAgg
from x_model.types import BaseUpd
from xync_schema.enums import PmType, Side, AdStatus, OrderStatus
from xync_schema.models import Country, Pm, Ex, CredEx, Cur
from xync_schema.xtype import PmExBank

from xync_client.pm_unifier import PmUni

DictOfDicts = dict[int | str, dict]
ListOfDicts = list[dict]
FlatDict = dict[int | str, str]
MapOfIdsList = dict[int | str, list[int | str]]


class RemapBase(BaseModel):
    # Переопределяешь это в наследнике:
    _remap: ClassVar[dict[str, dict]] = {}

    @model_validator(mode="before")
    def _map_in(cls, data):
        data = dict(data)
        for field, mapping in cls._remap.items():
            if field in data:
                data[field] = mapping.get(data[field], data[field])
        return data

    @model_serializer
    def _map_out(self, srlz_info: SerializationInfo):
        data = dict(self)
        if srlz_info.by_alias:
            for field, mapping in self._remap.items():
                reverse = {v: k for k, v in mapping.items()}
                if field in data:
                    data[field] = reverse.get(data[field], data[field])
        return data


class PmTrait:
    typ: PmType | None = None
    logo: str | None = None
    banks: list[PmExBank] | None = None


class PmEx(BaseModel, PmTrait):
    exid: int | str
    name: str


class PmIn(BaseUpd, PmUni, PmTrait):
    _unq = "norm", "country"
    country: Country | None = None

    class Config:
        arbitrary_types_allowed = True


class PmExIn(BaseModel):
    pm: Pm
    ex: Ex
    exid: int | str
    name: str

    class Config:
        arbitrary_types_allowed = True


class BaseActor(BaseModel):
    exid: int | str
    nick: str | None = None


class BaseCounteragent(BaseActor):
    name: str


class BaseCredEx(BaseModel):
    detail: str
    exid: int | str = Field(alias="id")
    extra: str | None = None
    name: str
    pmex_exid: int | str
    curex_exid: int | str = None  # fills on outer BaseOrderFull validation hook
    seller: BaseCounteragent = None  # fills on outer BaseOrderFull validation hook

    async def guess_cur(self, curs: list[Cur] = None):
        curs = {c.ticker: c.id for c in curs or await Cur.all()}
        for cur, cid in curs.items():
            if re.search(re.compile(rf"\({cur}\)"), self.extra + self.detail):
                return cid
        lower_extras = [mb.lower() for mb in self.extra.split(" | ")]
        if (
            pms := await Pm.filter(Q(join_type="OR", pmexs__name__in=lower_extras, norm__in=self.extra.split(" | ")))
            .group_by("pmcurs__cur_id", "pmcurs__cur__ticker")
            .annotate(ccnt=Count("id"), names=ArrayAgg("norm"))
            .order_by("-ccnt", "pmcurs__cur__ticker")
            .values("pmcurs__cur_id", "names", "ccnt")
        ):
            return pms[0]["pmcurs__cur_id"]
        return None


class BaseAd(BaseModel):
    amount: float | None = None
    auto_msg: str | None = None
    cond_txt: str
    created_at: int  # utc(0) seconds
    coinex_exid: int | str
    curex_exid: int | str
    exid: int | str = Field(alias="id")
    maker_exid: int | str
    maker_name: str
    maker: BaseActor = None
    max_fiat: int
    min_fiat: int
    # paymentPeriod: int
    pmex_exids: list[int | str]
    premium: float
    price: float
    quantity: float | None = None
    # recentOrderNum: int
    side: Literal[Side.BUY, Side.SALE]
    status: Literal[AdStatus.active, AdStatus.defActive, AdStatus.soldOut]  # 10: online; 20: offline; 30: completed

    @model_validator(mode="after")
    def amount_or_quantity_required(self):
        if not self.amount and not self.quantity:
            raise ValueError("either amount or quantity is required")
        self.maker = BaseActor(exid=self.maker_exid, nick=self.maker_name and self.maker_name)
        return self


class BaseCredexsExidsTrait:
    credex_exids: list[int]


class BaseCredexsTrait:
    credex_exids: list[BaseCredEx]


class GetAdsReq(BaseModel):
    coin_id: int | str
    cur_id: int | str
    is_sell: bool
    pm_ids: list[int | str] = []
    amount: int | None = None
    vm_only: bool = False
    limit: int = 20
    page: int = 1
    # todo: add?
    # canTrade: bool = False
    # userId: str = ""  # int
    # verificationFilter
    kwargs: dict = {}


class AdUpdReq(BaseAd, GetAdsReq):
    price: float
    pm_ids: list[int | str]
    amount: float
    max_amount: float | None = None
    premium: float | None = None
    credexs: list[CredEx] | None = None
    quantity: float | None = None
    cond: str | None = None

    class Config:
        arbitrary_types_allowed = True


class BaseOrder(BaseModel):
    ad__pair_side__is_sell: bool  # int: 0 покупка, 1 продажа (именно для меня - апи агента, и пох мейкер я или тейкер)
    created_at: int
    exid: int = Field(alias="id")
    my_exid: int | None = None  # апи агент юзер
    status: OrderStatus


class BaseOrderItem(BaseOrder):
    amount: float | None = None
    pmex_exid: int | str = None  # int
    quantity: float | None = None
    ctr_exid: int | None = None  # контрагент
    ctr_nick: str | None = None
    taker_exid: int | None = None  # в байбите нету
    curex_exid: int | str = None
    coinex_exid: int | str = None
    seller_name: str
    buyer_name: str

    @model_validator(mode="after")
    def amount_or_quantity_required(self):
        if not self.amount and not self.quantity:
            raise ValueError("either amount or quantity is required")
        return self


class BaseOrderFull(BaseOrderItem):
    ad_id: int | str
    ad__maker_exid: int | None = None
    credex: BaseCredEx
    my_nick: str = Field(alias="nickName")
    taker: BaseCounteragent = None  # fills on validation hook


class BaseOrderReq(BaseModel):
    ad_id: int | str

    quantity: float | None = None
    amount: float | None = None

    pmex_exid: str = None  # int

    is_sell: bool = None
    cur_exid: int | str = None
    coin_exid: int | str = None
    coin_scale: int = None


class BaseOrderPaidReq(BaseModel):
    ad_id: int | str

    cred_id: int | None = None
    pm_id: int | None = None  # or pmcur_id?

    @model_validator(mode="after")
    def check_a_or_b(self):
        if not self.cred_id and not self.pm_id:
            raise ValueError("either cred_id or pm_id is required")
        return self
