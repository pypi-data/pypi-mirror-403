# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-flight-helper
# FileName:     http_schema.py
# Description:  http请求参数基础模型
# Author:       ASUS
# CreateDate:   2026/01/13
# Copyright ©2011-2026. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, PositiveInt, NonNegativeInt


class HTTPRequestDTO(BaseModel):
    # 平台信息
    http_domain: Optional[str] = Field(default=None, description="平台域名，例如：www.ceair.com")
    http_protocol: Optional[str] = Field(default=None, description="平台协议，例如：https")
    storage_state: Optional[Dict[str, Any]] = Field(
        default=None, description="playwright 爬取的用户登录状态没礼貌包含了cookie和origin"
    )
    timeout: Optional[PositiveInt] = Field(default=60, description="请求超时时间")
    retry: Optional[NonNegativeInt] = Field(default=0, description="重试次数")
    enable_log: Optional[bool] = Field(default=True, description="是否打印日志")
    token: Optional[str] = Field(default=None, description="token值")
    json_data: Optional[Dict[str, Any]] = Field(default=None, description="json参数")
    params_data: Optional[Dict[str, Any]] = Field(default=None, description="params参数")
    data: Optional[Dict[str, Any]] = Field(default=None, description="data参数")
    proxy: Optional[Dict[str, Any]] = Field(default=None, description="http的代理配置")
    headers: Optional[Dict[str, Any]] = Field(default=None, description="自定义的http headers")
