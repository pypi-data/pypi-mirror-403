from datetime import datetime
from enum import IntEnum
from typing import Literal, ClassVar

from pydantic import BaseModel, Field, model_validator
from xync_schema.enums import OrderStatus

from xync_client.Abc.xtype import RemapBase, BaseOrderItem, BaseOrderFull, BaseCounteragent
from xync_client.Bybit.etype.cred import CredEpyd, PaymentTerm as CredPaymentTerm, PaymentConfigVo, CredEx


class TopicWs(IntEnum):
    OTC_ORDER_STATUS = 1
    OTC_USER_CHAT_MSG_V2 = 2
    SELLER_CANCEL_CHANGE = 3


class Status(IntEnum):
    ws_new = 1
    # chain = 5  # waiting for chain (only web3)
    created = 10  # waiting for buyer to pay
    paid = 20  # waiting for seller to release
    appealed = 30  # appealing
    # appealed_by_buyer = 30  # the same appealing
    canceled = 40  # order cancelled
    completed = 50  # order finished
    # a = 60  # paying (only when paying online)
    # a = 70  # pay fail (only when paying online)
    # a = 80  # exception cancelled (the coin convert to other coin only hotswap)
    # a = 90  # waiting for buyer to select tokenId
    appeal_disputed = 100  # objectioning
    appeal_dispute_disputed = 110  # waiting for the user to raise an objection


class TakeAdReq(BaseModel):
    ad_id: int | str
    amount: float
    is_sell: bool
    pm_id: int
    coin_id: int
    cur_id: int
    quantity: float | None = None
    price: float | None = None


class OrderRequest(BaseModel):
    itemId: str
    tokenId: str
    currencyId: str
    side: Literal["0", "1"]  # 0 покупка, # 1 продажа
    curPrice: str
    quantity: str
    amount: str
    flag: Literal["amount", "quantity"]
    version: str = "1.0"
    securityRiskToken: str = ""
    isFromAi: bool = False


class OrderSellRequest(OrderRequest):
    paymentId: str
    paymentType: str


class PreOrderResp(BaseModel):
    id: str  # bigint
    price: str  # float .cur.scale
    lastQuantity: str  # float .coin.scale
    curPrice: str  # hex 32
    lastPrice: str  # float .cur.scale # future
    isOnline: bool
    lastLogoutTime: str  # timestamp(0)+0
    payments: list[str]  # list[int]
    status: Literal[10, 15, 20]
    paymentTerms: list  # empty
    paymentPeriod: Literal[15, 30, 60]
    totalAmount: str  # float .cur.scale
    minAmount: str  # float .cur.scale
    maxAmount: str  # float .cur.scale
    minQuantity: str  # float .coin.scale
    maxQuantity: str  # float .coin.scale
    itemPriceAvailableTime: str  # timestamp(0)+0
    itemPriceValidTime: Literal["45000"]
    itemType: Literal["ORIGIN"]
    shareItem: bool  # False


class OrderResp(BaseModel):
    orderId: str
    isNeedConfirm: bool
    confirmId: str = ""
    success: bool
    securityRiskToken: str = ""
    riskTokenType: Literal["challenge", ""] = ""
    riskVersion: Literal["1", "2", ""] = ""
    needSecurityRisk: bool
    isBulkOrder: bool
    confirmed: str = None
    delayTime: str


class CancelOrderReq(BaseModel):
    orderId: str
    cancelCode: Literal["cancelReason_transferFailed"] = "cancelReason_transferFailed"
    cancelRemark: str = ""
    voucherPictures: str = ""


class JudgeInfo(BaseModel):
    autoJudgeUnlockTime: str
    dissentResult: str
    preDissent: str
    postDissent: str


class Extension(BaseModel):
    isDelayWithdraw: bool
    delayTime: str
    startTime: str


class AppraiseInfo(BaseModel):
    anonymous: str
    appraiseContent: str
    appraiseId: str
    appraiseType: str
    modifyFlag: str
    updateDate: datetime | None

    @model_validator(mode="before")  # todo: separate to common part, and special bybit only part
    def empty_date(self):
        # noinspection PyTypeChecker
        if not self["updateDate"]:
            self["updateDate"] = None
        return self


class PaymentTerm(CredPaymentTerm):
    paymentConfigVo: PaymentConfigVo
    ruPaymentPrompt: bool


class _BaseOrder(RemapBase):
    _remap: ClassVar[dict[str, dict]] = {
        "status": {
            Status.ws_new: OrderStatus.created,
            Status.created: OrderStatus.created,
            Status.paid: OrderStatus.paid,
            Status.appealed: OrderStatus.appealed_by_seller,  # all appeals from bybit marks as appealed_by_seller
            Status.canceled: OrderStatus.canceled,
            Status.completed: OrderStatus.completed,
            Status.appeal_disputed: OrderStatus.appeal_disputed,  # appeal_disputed and appeal_dispute_disputed from bybit
            Status.appeal_dispute_disputed: OrderStatus.appeal_disputed,  # marks as just appeal_disputed
        }
    }
    ad__pair_side__is_sell: bool = Field(
        alias="side"
    )  # int: 0 покупка, 1 продажа (именно для меня - апи агента, и пох мейкер я или тейкер)
    created_at: int = Field(alias="createDate")


class _BaseChange(_BaseOrder):
    exid: int = Field(alias="id")
    my_exid: int | None = None  # апи агент юзер

    ad__maker_exid: int = Field(alias="makerUserId")
    appealedTimes: int
    user_exid: int = Field(alias="userId")  # todo: define: is it initiator or counteragent?
    totalAppealedTimes: int


class OrderItem(_BaseOrder, BaseOrderItem):
    my_exid: int = Field(alias="userId")
    coinex_exid: str = Field(alias="tokenId")
    orderType: Literal[
        "ORIGIN", "SMALL_COIN", "WEB3"
    ]  # str: ORIGIN: normal p2p order, SMALL_COIN: HotSwap p2p order, WEB3: web3 p2p order
    amount: float
    curex_exid: str = Field(alias="currencyId")
    price: float
    # notifyTokenQuantity: str
    # notifyTokenId: str
    fee: float
    ctr_nick: str = Field(alias="targetNickName")
    ctr_exid: int = Field(alias="targetUserId")
    selfUnreadMsgCount: str
    # transferLastSeconds: str
    # appealLastSeconds: str
    seller_name: str = Field(alias="sellerRealName")
    buyer_name: str = Field(alias="buyerRealName")
    # judgeInfo: JudgeInfo
    unreadMsgCount: str
    # extension: Extension
    # bulkOrderFlag: bool


class OrderFull(OrderItem, BaseOrderFull):
    ad_id: int = Field(alias="itemId")
    ad__maker_exid: int = Field(alias="makerUserId")
    my_nick: str = Field(alias="nickName")
    # targetAccountId: str
    # targetFirstName: str
    # targetSecondName: str
    targetUserAuthStatus: int
    targetConnectInformation: str
    # payerRealName: str  # todo: why? we have sellerRealName already
    tokenName: str
    quantity: float
    payCode: str
    paymentType: int
    updated_at: int = Field(alias="updateDate")
    transferDate: int
    paymentTermList: list[CredEpyd]
    remark: str
    recentOrderNum: int
    recentExecuteRate: int
    appealContent: str
    appealType: int
    appealNickName: str
    canAppeal: str
    totalAppealTimes: str
    paymentTermResult: CredEpyd
    credex: CredEx = Field(alias="confirmedPayTerm")
    appealedTimes: str
    orderFinishMinute: int
    makerFee: str
    takerFee: str
    showContact: bool
    contactInfo: list[str]
    tokenBalance: float
    fiatBalance: float
    # judgeType: str
    # canReport: bool
    # canReportDisagree: bool
    # canReportType: list[str]
    # canReportDisagreeType: list[str]
    appraiseStatus: str
    appraiseInfo: AppraiseInfo
    # canReportDisagreeTypes: list[str]
    # canReportTypes: list[str]
    # middleToken: str
    # beforePrice: str
    # beforeQuantity: str
    # beforeToken: str
    # alternative: str
    appealUserId: str
    cancelResponsible: str
    # chainType: str
    # chainAddress: str
    tradeHashCode: str
    # estimatedGasFee: str
    # gasFeeTokenId: str
    # tradingFeeTokenId: str
    # onChainInfo: str
    transactionId: str
    displayRefund: str
    # chainWithdrawLastSeconds: str
    # chainTransferLastSeconds: str
    orderSource: str
    cancelReason: str
    # sellerCancelExamineRemainTime: str
    # needSellerExamineCancel: bool
    # couponCurrencyAmount: str
    # totalCurrencyAmount: str
    # usedCoupon: bool  # bool: 1: used, 2: no used
    # couponTokenId: str
    # couponQuantity: str
    # completedOrderAppealCount: int
    # totalCompletedOrderAppealCount: int
    # realOrderStatus: int
    # appealVersion: int
    # helpType: str
    # appealFlowStatus: str
    # appealSubStatus: str
    # targetUserType: str
    # targetUserDisplays: list[str]
    # appealProcessChangeFlag: bool
    # appealNegotiationNode: int

    @model_validator(mode="after")  # todo: separate to common part, and special bybit only part
    def users_cred_cur(self):
        status_upd_map = {
            OrderStatus.created: "created_at",
            OrderStatus.paid: "transferDate",
        }
        if dt_field := status_upd_map.get(self.status):
            self.updated_at = getattr(self, dt_field)
        mc_exids = self.my_exid, self.ctr_exid
        mc_nicks = self.my_nick, self.ctr_nick
        sb_names = self.seller_name, self.buyer_name
        im_maker = self.ad__maker_exid == self.my_exid
        im_seller = self.ad__pair_side__is_sell == im_maker
        taker_exid = mc_exids[int(im_maker)]  # if im maker, then ctr(mc_exids[1]) - taker;
        taker_nick = mc_nicks[int(im_maker)]
        taker_name = sb_names[int(im_seller)]  # if im seller(im_maker==ad__is_sell), then taker(sb_names[1]) - buyer;
        seller_exid = mc_exids[int(not im_seller)]  # if im buyer, then ctr(mc_exids[1]) - seller;
        seller_nick = mc_nicks[int(not im_seller)]
        self.taker = BaseCounteragent(
            exid=taker_exid,
            nick=taker_nick,
            name=taker_name,
        )
        if self.credex:  # по дефолту в credex confirmedPayTerm
            if not self.credex.pmex_exid:  # но если там пусто, берем из paymentTermResult
                self.credex = CredEx.model_validate(self.paymentTermResult)
            if not self.credex.pmex_exid:  # а если и там пусто, то берем первый из paymentTermList
                self.credex = CredEx.model_validate(self.paymentTermList[0])
        self.credex.seller = BaseCounteragent(
            exid=seller_exid,
            nick=seller_nick,
            name=self.seller_name,
        )
        self.credex.curex_exid = self.curex_exid
        return self


class MsgFromApi(BaseModel):
    exid: int = Field(alias="id")
    # accountId: str
    message: str
    msgType: Literal[
        0, 1, 2, 5, 6, 7, 8
    ]  # int: 0: system message, 1: text (user), 2: image (user), 5: text (admin), 6: image (admin), 7: pdf (user), 8: video (user)
    msgCode: int
    created_at: int = Field(alias="createDate")
    isRead: Literal[0, 1]  # int: 1: read, 0: unread
    contentType: Literal["str", "pic", "pdf", "video"]
    roleType: str
    my_exid: int = Field(alias="userId")
    order_exid: str = Field(alias="orderId")
    msgUuid: str
    nickName: str
    read: Literal[0, 1]
    fileName: str
    onlyForCustomer: int | None = None


class StatusChange(_BaseChange):
    status: OrderStatus | None = None
    appealType: int = None  # 3 - I (seller) uploaded additional proofs # todo: выяснить другие значения
    appealVersion: int = None  # 3 - my (seller) appeal is accepted by support # todo: выяснить другие значения

    @model_validator(mode="after")
    def amount_or_quantity_required(self):
        if not self.status and not self.appealType and not self.appealVersion:
            raise ValueError("either status or appealVersion or appealType is required")
        if not self.status:
            if self.appealVersion == 3:
                self.status = OrderStatus.canceled
            elif self.appealType == 3:
                self.status = OrderStatus.appeal_disputed

        return self


class CountDown(_BaseChange):
    cancelType: Literal["ACTIVE", "TIMEOUT", ""]


class _BaseMsg(BaseModel):
    userId: int
    orderId: int
    message: str = None
    msgUuid: str
    msgUuId: str
    createDate: datetime
    contentType: str
    roleType: Literal["user", "sys", "alarm", "customer_support"]


class ReceiveMsgFromWs(_BaseMsg):
    id: int
    msgCode: int
    onlyForCustomer: int | None = None


class Read(_BaseMsg):
    readAmount: int
    read: Literal["1", "101", "110", "11", "111"]
    orderStatus: Status


class SellerCancelChange(BaseModel):
    userId: int
    makerUserId: int
    id: int
    createDate: datetime


class AdPostExcCode(IntEnum):
    FixPriceLimit = 912120022
    RareLimit = 912120050
    InsufficientBalance = 912120024
    Timestamp = 10002
    IP = 10010
    Quantity = 912300019
    PayMethod = 912300013
    Unknown = 912300014
