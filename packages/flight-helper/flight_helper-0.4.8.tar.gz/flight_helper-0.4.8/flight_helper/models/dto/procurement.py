# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-flight-helper
# FileName:     procurement.py
# Description:  采购信息数据转换对象
# Author:       ASUS
# CreateDate:   2026/01/08
# Copyright ©2011-2026. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, PositiveInt, NonNegativeFloat, Field


class ProcurementInputDTO(BaseModel):
    # 平台信息
    pl_domain: str = Field(..., description="平台域名，例如：www.ceair.com")
    pl_protocol: str = Field(..., description="平台协议，例如：https")
    out_ticket_platform_type: str = Field(..., description="出票平台类型")
    out_ticket_platform: str = Field(..., description="出票平台")
    account_number: str = Field(..., description="出票账号")
    type_name: str = Field(..., description="采购账号类型")
    purchase_account: str = Field(..., description="采购账号")
    pl_login_user: str = Field(..., description="采购平台登录账号")
    pl_login_password: str = Field(..., description="采购平台登录密码")
    remark: str = Field(..., description="备注，一般是由采购平台登录账号 + 采购平台登录密码拼接而成")

    out_ticket_account: Optional[str] = Field(default=None, description="账号")
    out_ticket_account_id: Optional[int] = Field(default=None, description="账号ID")
    out_ticket_account_password: Optional[str] = Field(default=None, description="密码")
    purchase_account_id: Optional[int] = Field(default=None, description="采购账号ID")
    out_ticket_platform_type_id: Optional[int] = Field(default=None, description="出票平台类型ID")
    out_ticket_mobile: Optional[str] = Field(default=None, description="出票手机，退改业务需要根据此手机号码来进行操作")


class ProcurementReusltDTO(BaseModel):
    # 平台信息
    order_no: PositiveInt = Field(..., description="报表平台的订单号")
    air_co_order_id: str = Field(..., description="官网订单号")
    transaction_amount: NonNegativeFloat = Field(..., description="采购金额")
    passenger_type: Literal["成人", "儿童", "婴儿"] = Field(
        ..., description="乘客类型，必须是：成人、儿童 或 婴儿"
    )

    passenger_names: Optional[List[str]] = Field(default=None, description="采购乘客")
    segment_index: Optional[PositiveInt] = Field(default=None, description="航段索引")
    flight_ids: Optional[str] = Field(default=None, description="乘客航段ID")
    passenger_ids: Optional[List[str]] = Field(default=None, description="乘客ID列表")
    pay_transaction: Optional[str] = Field(default=None, description="对账标识")


class FillProcurementInputDTO(ProcurementInputDTO, ProcurementReusltDTO):
    order_no: Optional[PositiveInt] = Field(default=None, description="报表平台的订单号")
    transaction_amount: Optional[NonNegativeFloat] = Field(default=None, description="采购金额")
    air_co_order_id: Optional[str] = Field(default=None, description="官网订单号")
