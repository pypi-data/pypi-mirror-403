from pydantic import BaseModel, Field, model_validator

from xync_client.Abc.xtype import BaseCredEx


class PaymentItem(BaseModel):
    view: bool
    name: str
    label: str
    placeholder: str
    type: str
    maxLength: str
    required: bool


class BasePaymentConf(BaseModel):
    paymentType: int
    paymentName: str


class PaymentConfig(BasePaymentConf):
    class PaymentTemplateItem(BaseModel):
        labelDialect: str
        placeholderDialect: str
        fieldName: str

    paymentDialect: str
    paymentTemplateItem: list[PaymentTemplateItem]


class PaymentConfigVo(BasePaymentConf):
    checkType: int
    sort: int
    addTips: str
    itemTips: str
    online: int
    items: list[dict[str, str | bool]]


class PaymentTerm(BaseModel):
    id: str  # int
    realName: str
    paymentType: int  # int
    bankName: str
    branchName: str
    accountNo: str
    qrcode: str
    visible: int
    payMessage: str
    firstName: str
    lastName: str
    secondLastName: str
    clabe: str
    debitCardNumber: str
    mobile: str
    businessName: str
    concept: str
    online: str = None
    paymentExt1: str
    paymentExt2: str
    paymentExt3: str
    paymentExt4: str
    paymentExt5: str
    paymentExt6: str
    paymentTemplateVersion: int


class MyPaymentTerm(PaymentTerm):
    paymentConfig: PaymentConfig
    realNameVerified: bool


class CredEpyd(PaymentTerm):
    securityRiskToken: str = ""


class MyCredEpyd(CredEpyd):  # todo: заменить везде где надо CredEpyd -> MyCredEpyd
    countNo: str
    hasPaymentTemplateChanged: bool
    paymentConfigVo: PaymentConfigVo  # only for my cred
    realNameVerified: bool
    channel: str
    currencyBalance: list[str]


class CredEx(BaseCredEx):
    detail: str = Field(alias="accountNo")
    extra: str | None = Field(alias="bankName")
    name: str = Field(alias="realName")
    pmex_exid: int = Field(alias="paymentType")

    @model_validator(mode="before")
    def xtr_fill(cls, data: PaymentTerm):
        data = dict(data)
        xtr = data["bankName"]
        if data["branchName"]:
            xtr += (" | " if xtr else "") + data["branchName"]
        if data["payMessage"]:
            xtr += (" | " if xtr else "") + data["payMessage"]
        if data["qrcode"]:
            xtr += (" | " if xtr else "") + data["qrcode"]
        if data["paymentExt1"]:
            xtr += (" | " if xtr else "") + data["paymentExt1"]
        data["bankName"] = xtr
        return data
