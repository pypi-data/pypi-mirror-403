# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-flight-helper
# FileName:     exception_utils.py
# Description:  异常类工具模块
# Author:       ASUS
# CreateDate:   2026/01/11
# Copyright ©2011-2026. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Literal, Dict, List, Any, Optional


class CancelPaymentError(Exception):
    def __init__(self, order_no: int):
        self.order_no = order_no
        super().__init__(f"订单<{order_no}>取消支付")


class DuplicatePaymentError(Exception):
    def __init__(self, order_no: int):
        self.order_no = order_no
        super().__init__(f"订单<{order_no}>重复支付")


class DuplicateBookingError(Exception):
    def __init__(self, message):
        super().__init__(message)


class NotEnoughTicketsError(Exception):
    def __init__(self, flight_no: str, seats_status: int, passengers: int):
        self.flight_no = flight_no
        self.seats_status = seats_status
        self.passengers = passengers
        super().__init__(f"采购平台显示航班<{flight_no}>的余票<{seats_status}>少于乘客人数<{passengers}>")


class ExcessiveProfitdError(Exception):
    def __init__(
            self, flight_no: str, query_price: float, order_price: float, reduction_threshold: float,
            asset: Literal["票面价", "销售价"] = "票面价"
    ):
        self.flight_no = flight_no
        self.query_price = query_price
        self.order_price = order_price
        self.reduction_threshold = reduction_threshold
        self.asset = asset
        super().__init__(
            f"航班<{flight_no}>采购平台价：{query_price} 低于：订单{asset}[{order_price}] - 下降阈值[{reduction_threshold}]，收益过高"
        )


class ExcessiveLossesError(Exception):
    def __init__(
            self, flight_no: str, query_price: float, order_price: float, increase_threshold: float,
            asset: Literal["票面价", "销售价"] = "票面价"
    ):
        self.flight_no = flight_no
        self.query_price = query_price
        self.order_price = order_price
        self.increase_threshold = increase_threshold
        self.asset = asset
        super().__init__(
            f"航班<{flight_no}>官网价：{query_price} 高于：订单{asset}[{order_price}] + 上浮阈值[{increase_threshold}]，亏损太多"
        )


class PaymentChannelError(Exception):
    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        super().__init__(f"支付渠道<{channel_name}>暂不支持")


class PaymentChannelMissError(Exception):
    def __init__(self):
        super().__init__(f"支付渠道参数丢失")


class PaymentTypeError(Exception):
    def __init__(self, payment_type: str):
        self.payment_type = payment_type
        super().__init__(f"付款方式<{payment_type}>暂不支持")


class PassengerTypeError(Exception):
    def __init__(self, passenger_type: str):
        self.passenger_type = passenger_type
        super().__init__(f"乘客类型<{passenger_type}>暂不支持")


class ProductTypeError(Exception):
    def __init__(self, product_type: str):
        self.product_type = product_type
        super().__init__(f"产品类型<{product_type}>暂不支持")


class HFPaymentTypeError(Exception):
    def __init__(self, payment_type: str):
        self.payment_type = payment_type
        super().__init__(f"汇付天下的付款方式<{payment_type}>暂不支持")


class YBPaymentTypeError(Exception):
    def __init__(self, payment_type: str):
        self.payment_type = payment_type
        super().__init__(f"易宝支付的付款方式<{payment_type}>暂不支持")

class Bill99PaymentTypeError(Exception):
    def __init__(self, payment_type: str):
        self.payment_type = payment_type
        super().__init__(f"快钱支付的付款方式<{payment_type}>暂不支持")


class PaymentFailedError(Exception):
    def __init__(self, pre_order_no: str, order_status: str):
        self.pre_order_no = pre_order_no
        self.order_status = order_status
        super().__init__(f"采购平台订单<{pre_order_no}>支付失败，支付结束后的状态<{order_status}>")


class PaymentFailError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class IPBlockError(Exception):

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RelationOrderConflictError(Exception):

    def __init__(self, message: str):
        super().__init__(message)


class LockedOrderFailedError(Exception):

    def __init__(self, message: str):
        super().__init__(message)


class OrderLimitError(Exception):
    def __init__(self, user_id: str, message: str):
        self.user_id = user_id
        super().__init__(f"用户<{user_id}>已受限，{message}")


class UserNotLoginError(Exception):

    def __init__(self, message: str):
        super().__init__(message)


class NonRrePaymentOprationStateError(Exception):
    """非待支付的操作状态错误，待支付的操作状态为：收款完成"""

    def __init__(self, order_id: int, stat_opration: str):
        self.order_id = order_id
        self.stat_opration = stat_opration
        super().__init__(f"当前订单操作状态已更新至[{stat_opration}]，停止预订支付")

class NonPaidCompletedStateError(Exception):
    """非支付完成的操作状态错误，回填票号的操作状态为：支付完成"""

    def __init__(self, order_id: int, stat_opration: str):
        self.order_id = order_id
        self.stat_opration = stat_opration
        super().__init__(f"当前订单操作状态已更新至[{stat_opration}]，无法回填票号")


class PassengerConsumptionLimitError(Exception):
    """乘客被法院限制消费"""

    def __init__(self, passengers: List[Dict[str, Any]], message: str):
        self.passengers = passengers
        self.message = message
        super().__init__(message)


class NotEnoughMoneyError(Exception):
    """账户余额不足"""

    def __init__(self, payment_type: Optional[str] = None, balance: Optional[float] = None):
        self.payment_type = payment_type
        self.balance = balance
        _msg: str = "账户余额不足"
        if payment_type is not None:
            _msg = f"付款方式：{payment_type}，{_msg}"
        if isinstance(balance, (float, int)):
            _msg = f"{_msg}，当前可用余额：{balance}"
        super().__init__(_msg)
