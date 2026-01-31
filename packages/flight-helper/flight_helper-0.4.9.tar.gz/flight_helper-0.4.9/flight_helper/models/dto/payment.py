# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-flight-helper
# FileName:     payment.py
# Description:  支付数据转成对象
# Author:       ASUS
# CreateDate:   2026/01/08
# Copyright ©2011-2026. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Literal, Optional, Union, Annotated
from pydantic import BaseModel, Field, TypeAdapter, NonNegativeFloat, PositiveInt

SupportedChannels = Literal["微信", "支付宝", "VISA", "易宝支付", "空中云汇", "快钱", "汇付天下", "快捷支付"]


class __BasePaymentDTO(BaseModel):
    channel_name: SupportedChannels = Field(..., description=f'支付渠道，只能是其中之一：{SupportedChannels}')
    payment_type: str = Field(..., description="支付方式")
    account: Optional[str] = Field(default=None, description="支付账号")
    password: Optional[str] = Field(default=None, description="账号密码")


class PaymentResultDTO(__BasePaymentDTO):
    order_no: PositiveInt = Field(..., description="报表平台订单号")
    pre_order_no: Optional[str] = Field(default=None, description="采购平台订单号")
    pay_transaction: Optional[str] = Field(default=None, description="支付流水")
    pay_amount: NonNegativeFloat = Field(default=0.0, description="支付金额")


class __BasePaymentInputDTO(__BasePaymentDTO):
    pay_domain: Optional[str] = Field(default=None, description="支付在线收银台域名，例如：www.ceair.com")
    pay_protocol: Optional[str] = Field(default=None, description="支付在线收银台协议，例如：https")


class YBAccountPaymentInputDTO(__BasePaymentInputDTO):
    """易宝支付-账号支付"""
    channel_name: Literal["易宝支付"] = Field(..., description="支付渠道")
    payment_type: Literal["账户支付"] = Field(..., description="支付方式")
    account: str = Field(..., description="易宝账号")
    password: str = Field(..., description="账号密码")


class WeChatPaymentInputDTO(__BasePaymentInputDTO):
    channel_name: Literal["微信"] = Field(..., description="支付渠道")
    payment_type: Literal["二维码识别"] = Field(..., description="支付方式")


class AlipayPaymentInputDTO(__BasePaymentInputDTO):
    channel_name: Literal["支付宝"] = Field(..., description="支付渠道")
    payment_type: Literal["二维码识别"] = Field(..., description="支付方式")


class HFPaidAccountPaymentInputDTO(__BasePaymentInputDTO):
    """汇付天下-付款账户支付"""
    channel_name: Literal["汇付天下"] = Field(..., description="支付渠道")
    payment_type: Literal["付款账户支付"] = Field(..., description="支付方式")
    account: str = Field(..., description="操作员号")
    password: str = Field(..., description="操作员交易密码")


class WallexVCCPaymentInputDTO(__BasePaymentInputDTO):
    """VISA-VCC支付"""
    channel_name: Literal["VISA"] = Field(..., description="支付渠道")
    payment_type: Literal["AIR_VCC", "YEE_VCC"] = Field(..., description="支付方式")


class Bill99AccountPaymentInputDTO(__BasePaymentInputDTO):
    """快钱-快钱账户支付"""
    channel_name: Literal["快钱"] = Field(..., description="支付渠道")
    payment_type: Literal["快钱账户"] = Field(..., description="支付方式")
    account: str = Field(..., description="快钱账户")


class WallexVCCPaymentInfoDTO(WallexVCCPaymentInputDTO):
    first_name: str = Field(..., description="名字")
    last_name: str = Field(..., description="姓氏")
    id_number: str = Field(..., description="证件号码")
    email: str = Field(..., description="电子邮箱")
    mobile: str = Field(..., description="手机号码")
    id_type: str = Field(..., description="证件类型")
    country: str = Field(..., description="国家/地区")
    state: str = Field(..., description="省/州")
    city: str = Field(..., description="城市")
    street: str = Field(..., description="街道名称")
    house_number: str = Field(..., description="门牌号码")
    postal_code: str = Field(..., description="邮编")
    card_number: Optional[str] = Field(default=None, description="卡号")
    expiry_year: Optional[PositiveInt] = Field(default=None, description="有效年份")
    expiry_month: Optional[PositiveInt] = Field(default=None, description="有效月份")
    card_id: Optional[str] = Field(default=None, description="虚拟卡ID")
    cvv: Optional[str] = Field(default=None, description="cvv")


class AirWallexVCCPaymentInfoDTO(WallexVCCPaymentInfoDTO):
    payment_type: Literal["AIR_VCC"] = Field(..., description="支付方式")


class YeeWallexVCCPaymentInfoDTO(WallexVCCPaymentInfoDTO):
    payment_type: Literal["YEE_VCC"] = Field(..., description="支付方式")


# 3. 创建联合类型，并指定 discriminator
PaymentInputDTO = Annotated[
    Union[
        YBAccountPaymentInputDTO,
        WeChatPaymentInputDTO,
        AlipayPaymentInputDTO,
        HFPaidAccountPaymentInputDTO,
        WallexVCCPaymentInputDTO,
        Bill99AccountPaymentInputDTO
        # TODO ... 其他支付方式
    ],
    Field(discriminator='channel_name')  # 或者用 'payment_type'，看业务
]

if __name__ == '__main__':
    # 创建适配器
    adapter = TypeAdapter(PaymentInputDTO)

    # 测试 1: 易宝支付
    yb_data = {
        "order_no": 1312312,
        "channel_name": "易宝支付",
        "payment_type": "账户支付",
        "account": "yb123",
        "password": "pass123",
        "pay_amount": 0.00
    }
    yb = PaymentResultDTO(**yb_data)
    print(yb)
    yb_payment = adapter.validate_python(yb_data)
    print(yb_payment)
    print(type(yb_payment))  # <class '__main__.YBAccountPayment'>

    # 测试 2: 微信支付
    wx_data = {
        "order_no": 1312312,
        "channel_name": "微信",
        "payment_type": "二维码识别",
        # account/password 可省略（Optional）
    }
    wx_payment = adapter.validate_python(wx_data)
    print(wx_payment)
    print(type(wx_payment))  # <class '__main__.WeChatPayment'>
