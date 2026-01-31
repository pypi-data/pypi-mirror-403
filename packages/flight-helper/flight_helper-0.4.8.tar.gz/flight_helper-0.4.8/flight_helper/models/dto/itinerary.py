# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-flight-helper
# FileName:     itinerary.py
# Description:  订单票号数据转换对象
# Author:       ASUS
# CreateDate:   2026/01/08
# Copyright ©2011-2026. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, NonNegativeFloat, Field, field_validator, PositiveInt


class ItineraryInfoDTO(BaseModel):
    # 平台信息
    passenger_name: str = Field(..., description="乘客名")
    order_itinerary: str = Field(..., description="行程单号")
    id_no: str = Field(..., description="证件号码")
    pre_order_no: str = Field(..., description="采购平台订单号")


class QueryItineraryResponseDTO(BaseModel):
    order_no: Optional[PositiveInt] = Field(default=None, description="业务平台订单号")
    pre_order_no: str = Field(..., description="采购平台订单号")
    order_status: Optional[str] = Field(default=None, description="采购平台订单状态")
    order_amount: NonNegativeFloat = Field(default=0.0, description="采购平台订单金额")
    cash_unit: Optional[str] = Field(default=None, description="采购金额的币种")
    itinerary_info: List[ItineraryInfoDTO] = Field(..., description="乘客行程单信息")

    @field_validator("itinerary_info")
    @classmethod
    def validate_non_empty(cls, v: List[ItineraryInfoDTO], info):
        if len(v) == 0:
            raise ValueError("至少需要一个乘客行程")
        # 获取外层的 pre_order_no
        outer_pre_order = info.data.get("pre_order_no")
        for item in v:
            if item.pre_order_no != outer_pre_order:
                raise ValueError("行程中的 pre_order_no 必须与订单一致")
        return v  # 必须返回值！


class QueryItineraryRequestDTO(BaseModel):
    # 平台信息
    payment_domain: Optional[str] = Field(default=None, description="采购平台域名，例如：www.ceair.com")
    payment_protocol: Optional[str] = Field(default=None, description="采购平台协议，例如：https")
    storage_state: Optional[Dict[str, Any]] = Field(
        default=None, description="playwright 爬取的用户登录状态没礼貌包含了cookie和origin"
    )
    token: Optional[str] = Field(default=None, description="token值")
    pre_order_no: str = Field(..., description="采购平台订单号")
    user_id: Optional[str] = Field(default=None, description="采购平台登录用户的ID")
    proxy: Optional[Dict[str, Any]] = Field(default=None, description="http的代理配置")
    headers: Optional[Dict[str, Any]] = Field(default=None, description="自定义的http headers")
