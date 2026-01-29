from enum import StrEnum, IntEnum
from typing import Optional, Any, Literal
from pydantic import BaseModel, Field, model_validator
from xync_client.Abc.xtype import BaseAd, AdStatus as xAdStatus, RemapBase, BaseCredexsExidsTrait
from xync_schema.enums import Side, PriceType


class AdStatus(IntEnum):
    active = 10
    hidden = 20
    complete = 30


class AdStatusReq(StrEnum):
    sold_out = "1"
    active = "2"


class AdsReq(BaseModel):
    tokenId: str = Field(validation_alias="coin_id")
    currencyId: str = Field(validation_alias="cur_id")
    side: Literal["0", "1"] = Field(validation_alias="is_sell")  # 0 покупка, # 1 продажа
    payment: list[str] = Field([], validation_alias="pm_ids")  # int
    size: str = Field("20", validation_alias="limit")  # int
    page: str = "1"  # int
    amount: str = ""  # float
    vaMaker: bool = Field(False, validation_alias="vm_only")
    canTrade: bool = False
    userId: str = ""  # int
    verificationFilter: Literal[0, 1, 2] = 0
    sortType: Literal["OVERALL_RANKING", "TRADE_VOLUME", "TRADE_COMPLETION_RATE", "TRADE_PRICE"] = "OVERALL_RANKING"
    paymentPeriod: Literal[[], [15], [30], [60]] = []
    itemRegion: int = 1
    bulkMaker: bool = False


class Currency(BaseModel):
    currencyId: str
    exchangeId: str
    id: str
    orgId: str
    scale: int


class Token(BaseModel):
    exchangeId: str
    id: str
    orgId: str
    scale: int
    sequence: int
    tokenId: str


class SymbolInfo(BaseModel):
    buyAd: Optional[Any]
    buyFeeRate: str
    currency: Currency
    currencyId: str
    currencyLowerMaxQuote: str
    currencyMaxQuote: str
    currencyMinQuote: str
    exchangeId: str
    id: str
    itemDownRange: str
    itemSideLimit: int
    itemUpRange: str
    kycCurrencyLimit: str
    lowerLimitAlarm: int
    orderAutoCancelMinute: int
    orderFinishMinute: int
    orgId: str
    sellAd: Optional[Any]
    sellFeeRate: str
    status: int
    token: Token
    tokenId: str
    tokenMaxQuote: str
    tokenMinQuote: str
    tradeSide: int
    upperLimitAlarm: int


class TradingPreferenceSet(BaseModel):
    completeRateDay30: str
    hasCompleteRateDay30: int
    hasNationalLimit: int
    hasOrderFinishNumberDay30: int
    hasRegisterTime: int
    hasUnPostAd: int
    isEmail: int
    isKyc: int
    isMobile: int
    nationalLimit: str
    orderFinishNumberDay30: int
    registerTimeThreshold: int


class AdPostRequest(BaseModel):
    tokenId: str
    currencyId: str
    side: Literal[0, 1]  # 0 - покупка, 1 - продажа
    priceType: Literal[0, 1]  # 0 - fix rate, 1 - floating
    premium: str
    price: str
    minAmount: str
    maxAmount: str
    remark: str
    tradingPreferenceSet: TradingPreferenceSet
    paymentIds: list[str]  # list[int]
    quantity: str  # float
    paymentPeriod: int = 15
    itemType: Literal["ORIGIN", "BULK"] = "ORIGIN"


class AdRequest(AdPostRequest, BaseAd):
    actionType: Literal["MODIFY", "ACTIVE"] = "MODIFY"


class Ad(BaseAd, RemapBase):
    _remap = {
        "status": {
            AdStatus.active: xAdStatus.active,
            AdStatus.hidden: xAdStatus.defActive,
            AdStatus.complete: xAdStatus.soldOut,
        }
    }

    auto_msg: None = None
    cond_txt: str = Field(alias="remark")
    created_at: int = Field(alias="createDate")
    coinex_exid: str = Field(alias="tokenId")  # ticker
    curex_exid: str = Field(alias="currencyId")  # ticker
    maker_exid: int = Field(alias="userId")
    maker_name: str = Field(alias="nickName")
    max_fiat: float = Field(alias="maxAmount")
    min_fiat: float = Field(alias="minAmount")
    # paymentPeriod: int
    pmex_exids: list[int] = Field(alias="payments")
    # recentOrderNum: int
    side: Literal[Side.BUY, Side.SALE]
    priceType: Literal[PriceType.FIX, PriceType.FLOAT]
    # tradingPreferenceSet: TradingPreferenceSet | None = None  # for initial actualize

    # accountId: str = None  # for initial actualize
    # authStatus: int = None  # for initial actualize
    # authTag: List[str] = None  # for initial actualize
    # ban: bool = None  # for initial actualize
    # baned: bool = None  # for initial actualize
    # blocked: str = None  # for initial actualize
    # createDate: str = None  # for initial actualize
    # executedQuantity: str = None  # for initial actualize
    # fee: str = None  # for initial actualize
    # finishNum: int = None  # for initial actualize
    # frozenQuantity: str = None  # for initial actualize
    # isOnline: bool = None  # for initial actualize
    # itemType: str = None  # for initial actualize
    # lastLogoutTime: str = None  # for initial actualize
    # lastQuantity: str = Field(serialization_alias="quantity")
    # makerContact: bool = None  # for initial actualize
    # nickName: str = None  # for initial actualize
    # orderNum: int = None  # for initial actualize
    # paymentPeriod: int = None  # for initial actualize
    # payments: List[str] = None  # for initial actualize
    # quantity: str = Field(serialization_alias="allQuantity")  # for initial actualize
    # recentExecuteRate: int = None  # for initial actualize
    # recentOrderNum: int = None  # for initial actualize
    # recommend: bool = None  # for initial actualize
    # recommendTag: str = None  # for initial actualize
    # status: Literal[10, 20, 30]  # 10: online; 20: offline; 30: completed
    # symbolInfo: SymbolInfo = None  # for initial actualize
    # tokenName: str = None  # for initial actualize
    # userMaskId: str = None  # for initial actualize
    # userType: str = None  # for initial actualize
    # verificationOrderAmount: str = None  # for initial actualize
    # verificationOrderLabels: List[Any] = None  # for initial actualize
    # verificationOrderSwitch: bool = None  # for initial actualize
    # version: int = None  # for initial actualize

    # @field_serializer("status")
    # def status(self, status, _info) -> xtype.AdStatus:
    #     return {10: xtype.AdStatus.active, 20: xtype.AdStatus.defActive, 30: xtype.AdStatus.soldOut}[status]


class MyAd(Ad, BaseCredexsExidsTrait):
    credex_exids: list[int] = Field(alias="paymentTerms")
    # paymentTerms: list[MyPaymentTerm]

    @model_validator(mode="before")
    def cred_exids(cls, data: "MyAd"):
        data["paymentTerms"] = [pt["id"] for pt in data["paymentTerms"]]
        return data
