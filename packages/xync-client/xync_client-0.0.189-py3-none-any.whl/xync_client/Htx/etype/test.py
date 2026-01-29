from pydantic import BaseModel, Field
from xync_client.Abc.xtype import BaseCredEx


class ModelField(BaseModel):
    fieldId: str
    name: str
    fieldType: str
    index: int
    maxLength: int
    required: bool
    copyable: bool
    remindWord: str
    valueType: str | None
    value: str | None


class BaseCredEpyd(BaseCredEx):
    id: int
    uid: int
    userName: str
    bankType: int
    bankNumber: str
    bankName: str
    bankAddress: str | None = None
    qrCode: str | None = None
    isShow: int
    buyingEnable: bool
    sellingEnable: bool
    disabledCurrencyList: list[int]
    modelFields: str
    modelFieldsList: list[ModelField]
    color: str
    payMethodName: str


class BaseCredExId(BaseCredEx):
    id: int = Field(validation_alias="bankId")


class Result(BaseModel):
    code: int
    data: BaseCredExId
    extend: str | None = None
    message: str
    success: bool
