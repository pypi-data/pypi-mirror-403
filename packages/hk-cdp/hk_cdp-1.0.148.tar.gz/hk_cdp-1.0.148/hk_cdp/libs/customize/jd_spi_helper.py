# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-08-15 14:29:08
@LastEditTime: 2026-01-15 17:51:57
@LastEditors: HuangJianYi
@Description: 京东SPI帮助类，用于生成和验证签名
"""
import hashlib
import traceback
from typing import Dict, Any
import uuid
import requests
import time
import json
from datetime import datetime
from seven_framework import CryptoHelper
from seven_cloudapp_frame.models.seven_model import *


class JdSpiHelper:
    """
    CDP SPI帮助类
    """
    @classmethod
    def spi_sign(self, params: Dict[str, Any], app_secret: str, debug_config: dict) -> str:
        """
        生成签名
        :param params: 请求参数字典
        :param app_secret: 应用秘钥
        :param debug_config: 调试配置
        :return: MD5签名字符串（大写）
        :return: MD5签名字符串（大写）
        """
        brand_id = params.get("brandId", "")
        is_debug = True if debug_config and debug_config.get("customer_id") == brand_id else False
        if is_debug is True:
            app_secret = CryptoHelper.md5_encrypt(app_secret).upper()
        # 第一步：过滤参数，只保留需要参与签名的参数
        filtered_params = {}
        for key, value in params.items():
            # token参数不参与计算
            if key == "token":
                continue
            # 值为None或空字符串的String类型不参与计算
            if value is None:
                continue
            # 检查值的类型
            if isinstance(value, str):
                # 空字符串不参与计算
                if value == "":
                    continue
                filtered_params[key] = value
            elif isinstance(value, (int, bool)):
                # Integer类型和Long类型（Python中int对应）参与计算
                # 注意：bool是int的子类，所以也需要处理
                filtered_params[key] = str(value)
            elif isinstance(value, (dict, list, tuple, set)):
                # Object及数组类型不参与计算
                continue
            else:
                # 其他类型转换为字符串尝试处理，或者根据需求跳过
                try:
                    # 尝试转换为字符串，如果转换后为空则跳过
                    str_value = str(value)
                    if str_value:
                        filtered_params[key] = str_value
                except Exception:
                    # 转换失败则跳过
                    continue
        # 第二步：按照参数名称的ASCII码表顺序排序
        # 使用collections.OrderedDict保持排序
        sorted_items = sorted(filtered_params.items(), key=lambda x: x[0])
        # 第三步：拼接参数字符串
        # 前面加上secret
        query = app_secret
        # 拼接排序后的参数
        for key, value in sorted_items:
            query += key + str(value)
        # 后面加上secret
        query += app_secret
        # 第四步：计算MD5
        # 使用UTF-8编码
        md5_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        # 转换为大写返回
        return md5_hash.upper()

    @classmethod
    def check_sign(self, params: Dict[str, Any], app_secret: str, debug_config: dict) -> bool:
        """
        生成签名
        :param params: 请求参数字典
        :param app_secret: 应用秘钥
        :param debug_config: 调试配置
        :return: True-签名正确，False-签名错误
        """
        # 获取原始token
        original_token = params.get("token", "")
        # 生成新token
        new_token = self.spi_sign(params, app_secret, debug_config)
        return original_token == new_token

    @classmethod
    def encrypt_mobile_md5(self, mobile: str, salt: str) -> str:
        """
        MD5加密手机号（32位大写）
        :param mobile: 明文手机号
        :param salt: 盐值
        :return: 32位大写MD5密文
        """
        if not mobile:
            return ""
        if salt:
            mobile += salt
        md5_hash = hashlib.md5(mobile.encode('utf-8')).hexdigest().upper()
        return md5_hash

    @classmethod
    def code_to_desc(self, code):
        if code == "0":
            return "调用成功"
        elif code == "9001":
            return "参数缺失，缺少必填参数"
        elif code == "9002":
            return "无效的 appkey"
        elif code == "9003":
            return "无效的 token"
        elif code == "9004":
            return "该 appkey 无该接口调用权限"
        elif code == "10001":
            return "会员不存在"
        elif code == "10002":
            return "店铺不存在"
        elif code == "10010":
            return "上翻的会员已存在，绑定的手机号不一致，不允许修改手机号"
        elif code == "999999":
            return "调用失败，未知错误"


class JdCdpClient:
    """
    CDP客户端
    """
    def __init__(self, base_url: str, app_key: str, secret: str, brand_id: str, context=None, logging_error=None, logging_info=None, debug_config={}):
        """
        初始化CDP客户端
        :param base_url: 域名地址
        :param app_key: 应用key
        :param secret: 应用密钥
        :param brand_id: 商家标识
        :param debug_config: {'brand_id': 联调品牌体系ID, "customer_id":"由营销云分配", "token":"由营销云分配"}
        """
        self.base_url = base_url
        self.app_key = app_key
        self.secret = secret
        self.brand_id = brand_id
        self.context = context
        self.debug_config = debug_config
        self.logging_link_error = logging_error
        self.logging_link_info = logging_info
        self.is_debug = True if self.debug_config and self.debug_config.get("customer_id") == self.brand_id else False

    def request(self, url: str, headers: Dict[str, str], params: Dict, business_name=None, is_log: bool = False):
        """
        发送POST请求
        :param url: 请求地址
        :param headers: 请求头
        :param params: 请求参数
        :param business_name: 业务名称
        :param is_log: 是否记录日志
        :return: invoke_result_data
        """
        try:
            invoke_result_data = InvokeResultData()
            if self.is_debug is True:
                # 联调环境添加联调参数
                headers["customerId"] = self.debug_config.get("customer_id")
                headers["token"] = self.debug_config.get("token")
                # 联调环境使用联调地址
                self.base_url = "https://membership-mock-pre.jdx.com"

            url = self.base_url + url
            log_info = ""
            if is_log is True:
                log_info = f'Request url:{url},Request headers:{headers},Request params:{json.dumps(params)};'
            response = requests.post(url=url, data=params, headers=headers, timeout=30)
            if is_log is True:
                log_info += f'Response status code: {response.status_code},Response headers:{response.headers},Response content:' + response.content.decode('utf-8')
                if self.context:
                    self.context.logging_link_info(log_info)
                elif self.logging_link_info:
                    self.logging_link_info(log_info)
            if not response:
                invoke_result_data.success = False
                invoke_result_data.error_code = "exception"
                invoke_result_data.error_message = "系统繁忙,请稍后再试"
                return invoke_result_data
            if response.status_code != 200:
                invoke_result_data.success = False
                invoke_result_data.error_code = "http_error"
                invoke_result_data.error_message = f"请求状态码：{response.status_code}"
                return invoke_result_data
            result = json.loads(response.content)
            if result['status'] != 0:
                invoke_result_data.success = False
                invoke_result_data.error_code = result['status']
                invoke_result_data.error_message = result.get('errMsg', '系统繁忙,请稍后再试')
                return invoke_result_data
            # 检查响应格式
            if "code" not in result or "data" not in result:
                invoke_result_data.success = False
                invoke_result_data.error_code = "exception"
                invoke_result_data.error_message = "code or data 字段缺失"
                return invoke_result_data
            if result["code"] != "0":
                invoke_result_data.success = False
                invoke_result_data.error_code = result["code"]
                if result["code"] == "999999":
                    invoke_result_data.error_message = result["msg"]
                else:
                    invoke_result_data.error_message = JdSpiHelper.code_to_desc(result["code"])
                return invoke_result_data
            if result['data']['retCode'] != "SUC":
                invoke_result_data.success = False
                invoke_result_data.error_code = result['data']['retCode']
                invoke_result_data.error_message = result["msg"]
                return invoke_result_data
            invoke_result_data.data = result
            return invoke_result_data
        except Exception as e:
            error_info = f"【{business_name}】" if business_name else ""
            error_info += traceback.format_exc()
            if self.context:
                self.context.logging_link_error(error_info)
            elif self.logging_link_error:
                self.logging_link_error(error_info)
            invoke_result_data.success = False
            invoke_result_data.error_code = "exception"
            invoke_result_data.error_message = "系统繁忙,请稍后再试"
            return invoke_result_data

    def member_reg_and_bind_v2(self, account: str, mix_mobile: str, extend: Dict[str, Any] = None, platform: str = "JD", ruid: str = None, is_log=False):
        """
        新接入品牌需要走新接口流程
        会员注册绑定接口(会员绑定功能于一体的接口，该接口调用就是要完成会员同步到CDP。当CRM调用该接口进行会员注册或者绑定的时，需要CDP对会员进行身份识别，如果没有注册过就注
        册，如果没有绑定过就走绑定逻辑。注意：当CRM向CDP注册会员成功的时候，会返回cdp的会员id，因为此时可能会员通中没有此会员，因此无法返回xid。同时，因为法务原因，会员通向CDP注册会员时不能使用明文手机号)
        :param account: CRM会员ID信息
        :param mix_mobile: 密文手机号
        :param extend: 扩展信息字典
        :param platform: 平台，例如："JD"
        :param ruid: 请求唯一ID，不传则自动生成
        :param is_log: 是否记录日志 True-记录日志，False-不记录日志
        :return: 接口响应结果{"code":"0","data":{"bind_status":0,"cardNumber":"20001","cdp_Id":"47","retCode":"SUC"},"msg":"请求成功"}}
        """
        # 接口URL
        url = "/CrmMemberV2/memberRegAndBindV2"
        # 生成请求ID
        if ruid is None:
            ruid = str(uuid.uuid4())
        # 构建请求体参数（不包含token）
        body_params = {
            "timestamp": int(time.time() * 1000),  # 毫秒时间戳
            "appkey": self.app_key,
            "brandId": self.brand_id,
            "account": account,
            "platform": platform,
            "mixMobile": mix_mobile
        }
        # 添加扩展信息
        if extend:
            if "register_time" not in extend.keys():
                invoke_result_data.success = False
                invoke_result_data.error_code = "param_error"
                invoke_result_data.error_message = "register_time必传"
                return invoke_result_data
            extend["register_time"] = str(extend["register_time"]).strftime("%Y-%m-%d %H:%M:%S") if isinstance(extend["register_time"], datetime) else extend["register_time"].strftime("%Y-%m-%d %H:%M:%S")
            body_params["extend"] = extend
        # 生成token（注意：token生成时不包含token字段本身）
        token = JdSpiHelper.spi_sign(body_params, self.secret, self.debug_config)
        # 将token添加到请求参数中
        body_params["token"] = token
        # 构建请求头
        headers = {"ruid": ruid, "Content-Type": "application/json"}
        # 发送POST请求
        invoke_result_data = self.request(url=url, headers=headers, json=body_params, business_name="会员注册绑定接口", is_log=is_log)
        return invoke_result_data

    def query_member_bind_status(self, account: str, mix_mobile: str = None, platform: str = "JD", ruid: str = None, is_log=False):
        """
        查询会员绑定状态(该接口的应用场景，当crm系统调用cdp进行注册绑定时，发生超时的时候，当前绑定流程会认为失败，在CDP系统可能已经入会成功，这个时候可以通过该接口进行查询对应的绑定状态，从而或其他处理，保证会员数据最终一致性。解绑)
        :param account: CRM会员ID信息
        :param mix_mobile: 密文手机号
        :param platform: 平台，例如："JD"
        :param ruid: 请求唯一ID，不传则自动生成
        :param is_log: 是否记录日志 True-记录日志，False-不记录日志
        :return: 接口响应结果({"msg": "用户已注册","code": "0","data": {"bind_status": 0,"retCode":"register","cardNumber": "30001","cdp_Id": "24"}})
        """
        # 接口URL
        url = "/CrmMember/queryMemberBindStatus"
        # 生成请求ID
        if ruid is None:
            ruid = str(uuid.uuid4())
        # 构建请求体参数（不包含token）
        body_params = {
            "timestamp": int(time.time() * 1000),  # 毫秒时间戳
            "appkey": self.app_key,
            "brandId": self.brand_id,
            "account": account,
            "platform": platform
        }
        if mix_mobile:
            body_params["mixMobile"] = mix_mobile
        # 生成token（注意：token生成时不包含token字段本身）
        token = JdSpiHelper.spi_sign(body_params, self.secret, self.debug_config)
        # 将token添加到请求参数中
        body_params["token"] = token
        # 构建请求头
        headers = {"ruid": ruid, "Content-Type": "application/json"}
        invoke_result_data = self.request(url=url, headers=headers, json=body_params, business_name="查询会员绑定状态接口", is_log=is_log)
        return invoke_result_data

    def modify_member_point_to_cdp(self, account: str, point: int, change_type: int, content: str, point_type: int, occur_time: str, extend: str = None, support_over_draft: bool = None, platform: str = "JD", ruid: str = None, is_log=False):
        """
        会员积分变更接口，若crm作为数据中心，当品牌crm需要变更会员积分时，需要品牌crm调用该接口将积分变更同步到cdp。
        注意：CRM客户需要调用调整积分接口来修改会员的积分，调整完积分后会实时同步给会员通。
        如果调用会员更新接口来传入总积分数量，则无法同步给会员通。
        :param account: CRM会员ID信息
        :param point: 积分值，是个正数
        :param change_type: “add”-增加 “sub”-扣减
        :param content: 积分变更描述信息
        :param point_type: 积分类型如果不在这个里面，则设置为0，并在content中添加积分变更类型信息.积分变更类型，如27=>‘发放积分’29=>‘店铺签到发放’30=>‘关注店铺发放’31=>‘互动积分发放’32=>‘其他渠道发放’26=>‘消费积分’33=>‘兑换优惠卷消耗’34=>‘兑换红包消耗’35=>‘兑换京豆消耗’36=>‘兑换其他权益消耗’37=>‘互动消耗积分’38=>‘手动调整
        :param occur_time: 积分变更时间，yyyy-MM-dd HH:mm:ss
        :param extend: 扩展信息
        :param support_over_draft: 是否支持积分扣负，不传默认不支持扣负
        :param platform: 平台，例如："JD"
        :param ruid: 请求唯一ID，不传则自动生成
        :param is_log: 是否记录日志 True-记录日志，False-不记录日志
        :return: 接口响应结果{"msg":"请求成功","code":"0","data": {"record_Id":"12","retCode":"SUC"}}
        """
        invoke_result_data = InvokeResultData()
        # 接口URL
        url = "/CrmMemberPoint/modifyMemberPointToCdp"
        # 生成请求ID
        if ruid is None:
            ruid = str(uuid.uuid4())
        # 构建请求体参数（不包含token）
        body_params = {
            "timestamp": int(time.time() * 1000),  # 毫秒时间戳
            "appkey": self.app_key,
            "brandId": self.brand_id,
            "account": account,
            "platform": platform,
            "point": point,
            "changeType": change_type,
            "content": content,
            "pointType": point_type,
            "occurTime": occur_time
        }
        if extend:
            body_params["extend"] = extend
        if support_over_draft:
            body_params["supportOverDraft"] = support_over_draft

        # 生成token（注意：token生成时不包含token字段本身）
        token = JdSpiHelper.spi_sign(body_params, self.secret, self.debug_config)
        # 将token添加到请求参数中
        body_params["token"] = token
        # 构建请求头
        headers = {"ruid": ruid, "Content-Type": "application/json"}
        invoke_result_data = self.request(url=url, headers=headers, json=body_params, business_name="会员积分变更接口", is_log=is_log)
        return invoke_result_data

    def modify_member_grade_to_cdp(self, account: str, expire_type: int, grade: int, content: str, type: int = 38, start_time: str = None, end_time: str = None, platform: str = "JD", ruid: str = None, is_log=False):
        """
        当会员的等级数据中心在CRM的时候，需要调用CDP提供的接口同步用户的等级。注意：调整会员等级接口非必需调用
        :param account: CRM会员ID信息
        :param expire_type: 等级过期类型,1:无限期 2:固定时间 3:领取后一定时间
        :param grade: 将用户调整到该等级
        :param content: 文本说明等级变更原因
        :param type: 固定传入38，代表人工调整
        :param start_time: 等级有效期开始时间，如果等级过期类型不是无限期，这个字段需要传入
        :param end_time: 等级有效期结束时间，如果等级过期类型不是无限期，这个字段需要传入
        :param platform: 平台，例如："JD"
        :param ruid: 请求唯一ID，不传则自动生成
        :param is_log: 是否记录日志 True-记录日志，False-不记录日志
        :return: 接口响应结果{"msg":"请求成功","code":"0","data": {"record_Id":"100","retCode":"SUC"}}
        """
        invoke_result_data = InvokeResultData()
        # 接口URL
        url = "/CrmMemberGrade/adjustMemberGradeToCDP"
        # 生成请求ID
        if ruid is None:
            ruid = str(uuid.uuid4())
        # 构建请求体参数（不包含token）
        body_params = {
            "timestamp": int(time.time() * 1000),  # 毫秒时间戳
            "appkey": self.app_key,
            "brandId": self.brand_id,
            "account": account,
            "platform": platform,
            "expire_type": expire_type,
            "grade": grade,
            "content": content,
            "type": type
        }
        if start_time:
            body_params["start_time"] = start_time
        if end_time:
            body_params["end_time"] = end_time

        # 生成token（注意：token生成时不包含token字段本身）
        token = JdSpiHelper.spi_sign(body_params, self.secret, self.debug_config)
        # 将token添加到请求参数中
        body_params["token"] = token
        # 构建请求头
        headers = {"ruid": ruid, "Content-Type": "application/json"}
        invoke_result_data = self.request(url=url, headers=headers, json=body_params, business_name="会员等级变更接口", is_log=is_log)
        return invoke_result_data

    def member_unbind(self, account: str, platform: str = "JD", ruid: str = None, is_log=False):
        """
        CRM会员解绑接口。原状态为CRM已注册的变为线上线下都未注册，原状态为已绑定的变为会员通已注册。如下：全域会员，若CRM发起解绑，则会员状态变为 仅京东会员：1；仅一方会员，若CRM发起解绑，则会员状态变为 解绑会员：3；注意此接口不支持crm解绑京东会员身份，仅指解绑一方渠道会员，京东会员身份仅能由京东发起解绑
        :param account: CRM会员ID信息
        :param platform: 平台，例如："JD"
        :param ruid: 请求唯一ID，不传则自动生成
        :param is_log: 是否记录日志 True-记录日志，False-不记录日志
        :return: 接口响应结果{ "code": "0", "data": { "bind_status": 3, "cardNumber": "20001", "retCode":"SUC" }, "msg": "请求成功"}
        """
        invoke_result_data = InvokeResultData()
        # 接口URL
        url = "/CrmMember/memberUnbind"
        # 生成请求ID
        if ruid is None:
            ruid = str(uuid.uuid4())
        # 构建请求体参数（不包含token）
        body_params = {
            "timestamp": int(time.time() * 1000),  # 毫秒时间戳
            "appkey": self.app_key,
            "brandId": self.brand_id,
            "account": account,
            "platform": platform
        }
        # 生成token（注意：token生成时不包含token字段本身）
        token = JdSpiHelper.spi_sign(body_params, self.secret, self.debug_config)
        # 将token添加到请求参数中
        body_params["token"] = token
        # 构建请求头
        headers = {"ruid": ruid, "Content-Type": "application/json"}
        invoke_result_data = self.request(url=url, headers=headers, json=body_params, business_name="CRM会员解绑接口", is_log=is_log)
        return invoke_result_data

    def query_member_point(self, account: str, platform: str = "JD", ruid: str = None, is_log=False):
        """
        CRM调用CDP接口获取用户线上积分余额(可通过此接口查询会员在京东域内的当前积分值)
        :param account: CRM会员ID信息
        :param platform: 平台，例如："JD"
        :param ruid: 请求唯一ID，不传则自动生成
        :param is_log: 是否记录日志 True-记录日志，False-不记录日志
        :return: 接口响应结果{ "msg":"请求成功","code":"0","data": {"account": "testId","point": 200}}
        """
        invoke_result_data = InvokeResultData()
        # 接口URL
        url = "/CrmMemberPoint/queryMemberPoint"
        # 生成请求ID
        if ruid is None:
            ruid = str(uuid.uuid4())
        # 构建请求体参数（不包含token）
        body_params = {
            "timestamp": int(time.time() * 1000),  # 毫秒时间戳
            "appkey": self.app_key,
            "brandId": self.brand_id,
            "account": account,
            "platform": platform
        }
        # 生成token（注意：token生成时不包含token字段本身）
        token = JdSpiHelper.spi_sign(body_params, self.secret, self.debug_config)
        # 将token添加到请求参数中
        body_params["token"] = token
        # 构建请求头
        headers = {"ruid": ruid, "Content-Type": "application/json"}
        invoke_result_data = self.request(url=url, headers=headers, json=body_params, business_name="CRM调用CDP接口获取用户线上积分余额接口", is_log=is_log)
        return invoke_result_data

    def query_member_point_detail(self, account: str, page: int, page_size: int, start_time: str, end_time: str, start_row_key: str = None, platform: str = "JD", ruid: str = None, is_log=False):
        """
        CRM调用CDP接口获取用户线上积分明细(可通过此接口查询会员在京东域内的积分明细数据)
        :param account: CRM会员ID信息
        :param page: 分页页标，第一页为1，暂时可以固定填写为1，使用startRowKey替代
        :param pageSize: 分页大小，最大值50，超过提示该会员不存在
        :param startTime: 查询的明细开始时间：yyyyMMddHHHmmss
        :param endTime: 查询的明细结束时间：yyyyMMddHHmmss
        :param startRowKey: 分页查询使用，填入上一页返回中的nextRowKey，首页不需要填写
        :param platform: 平台，例如："JD"
        :param ruid: 请求唯一ID，不传则自动生成
        :param is_log: 是否记录日志 True-记录日志，False-不记录日志
        :return: 接口响应结果{"code":"0","data":{"data":[{"account":"1121","businessId":"50d7c95feb-371c-4d888034-21c81eba4f42","curPoints":250,"msg":"JOS初始化自带积分","occurTime":"2022-11-10 17:40:43","points":62,"sourceType":50},{"account":"1121","businessId":"50b3ccece7fb32-421b-a336-7d56f461e2b3","curPoints":188,"msg":"JOS初始化自带积分","occurTime":"2022-11-10 17:39:29","points":0,"sourceType":50}],"nextRowKey":"xxxx"},"msg":"查询成功"}
        """
        invoke_result_data = InvokeResultData()
        # 接口URL
        url = "/CrmMemberPoint/queryMemberPointDetail"
        # 生成请求ID
        if ruid is None:
            ruid = str(uuid.uuid4())
        # 构建请求体参数（不包含token）
        body_params = {
            "timestamp": int(time.time() * 1000),  # 毫秒时间戳
            "appkey": self.app_key,
            "brandId": self.brand_id,
            "account": account,
            "platform": platform,
            "page": page,
            "pageSize": page_size,
            "startTime": start_time,
            "endTime": end_time
        }
        if start_row_key:
            body_params["startRowKey"] = start_row_key
        # 生成token（注意：token生成时不包含token字段本身）
        token = JdSpiHelper.spi_sign(body_params, self.secret, self.debug_config)
        # 将token添加到请求参数中
        body_params["token"] = token
        # 构建请求头
        headers = {"ruid": ruid, "Content-Type": "application/json"}
        invoke_result_data = self.request(url=url, headers=headers, json=body_params, business_name="CRM调用CDP接口获取用户线上积分明细接口", is_log=is_log)
        return invoke_result_data

    def pin2xid_v2(self, pin: str, platform: str = "JD", ruid: str = None, is_log=False):
        """
        商家CRM通过此接口实现明文pin转xid。备注：需要此接口的品牌，需联系营销云开通白名单后使用
        :param pin: 需要转换的明文京东PIN
        :param platform: 平台，例如："JD"
        :param ruid: 请求唯一ID，不传则自动生成
        :param is_log: 是否记录日志 True-记录日志，False-不记录日志
        :return: 接口响应结果{"result":{"xid":"o*AAS6FTma2YJqif6pTrgCzcqbNWI0ZggYmuZKiEc8KDR3y_ZMLAU"},"status":"0", "errMsg":""}
        """
        invoke_result_data = InvokeResultData()
        # 接口URL
        url = "/CrmMember/pin2xidV2"
        # 生成请求ID
        if ruid is None:
            ruid = str(uuid.uuid4())
        # 构建请求体参数（不包含token）
        body_params = {
            "timestamp": int(time.time() * 1000),  # 毫秒时间戳
            "appkey": self.app_key,
            "brandId": self.brand_id,
            "pin": pin,
            "platform": platform
        }
        # 生成token（注意：token生成时不包含token字段本身）
        token = JdSpiHelper.spi_sign(body_params, self.secret, self.debug_config)
        # 将token添加到请求参数中
        body_params["token"] = token
        # 构建请求头
        headers = {"ruid": ruid, "Content-Type": "application/json"}
        invoke_result_data = self.request(url=url, headers=headers, params=body_params, business_name="pin转xid接口", is_log=is_log)
        return invoke_result_data








# # 使用示例
# if __name__ == "__main__":
#     # 配置参数
#     CDP_BASE_URL = "https://cdp.example.com"  # CDP服务器地址
#     APP_KEY = "your_app_key"  # 从CDP获取
#     SECRET = "your_secret_key"  # 从CDP获取
#     BRAND_ID = "your_brand_id"  # 商家标识

#     # 创建CDP客户端
#     cdp_client = CDPClient(base_url=CDP_BASE_URL, app_key=APP_KEY, secret=SECRET, brand_id=BRAND_ID)

#     # 示例1：简单会员注册绑定
#     print("示例1：简单会员注册绑定")

#     # 加密手机号
#     mobile = "13800138000"
#     encrypted_mobile = JdSpiHelper.encrypt_mobile_md5(mobile)
#     print(f"手机号加密结果: {encrypted_mobile}")

#     # 调用注册绑定接口
#     result = cdp_client.member_reg_and_bind(
#         account="CRM_001",  # CRM会员ID
#         platform="JD",  # 平台
#         mix_mobile=encrypted_mobile,  # 密文手机号
#         extend=None  # 无扩展信息
#     )

#     print(f"接口响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

#     # 示例2：带扩展信息的会员注册绑定
#     print("\n示例2：带扩展信息的会员注册绑定")

#     # 扩展信息
#     extend_info = {
#         "real_name": "张三",
#         "sex": 1,  # 1:男
#         "birthday": "1990-01-15",
#         "birth_type": 1,  # 1:公历
#         "email": "zhangsan@example.com",
#         "province": "北京",
#         "city": "北京市",
#         "district": "朝阳区",
#         "grade": 3,  # 会员等级
#         "point": 1000,  # 会员积分
#         "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     }

#     # 调用注册绑定接口
#     result2 = cdp_client.member_reg_and_bind(account="CRM_002", platform="JD", mix_mobile=JdSpiHelper.encrypt_mobile_md5("13900139000"), extend=extend_info)

#     print(f"接口响应: {json.dumps(result2, indent=2, ensure_ascii=False)}")

#     # 检查响应结果
#     if result2.get("code") == "0":
#         data = result2.get("data", {})
#         if data.get("retCode") == "SUC":
#             print("会员注册绑定成功！")
#             print(f"CDP会员ID: {data.get('cdp_Id', 'N/A')}")
#             print(f"绑定状态: {data.get('bind_status', 'N/A')}")
#         else:
#             print("会员注册绑定失败！")
#     else:
#         print(f"接口调用失败: {result2.get('msg')}")

#     # 示例3：批量处理会员注册绑定
#     print("\n示例3：批量处理会员注册绑定")

#     members = [{"account": "CRM_101", "mobile": "13800138101", "name": "李四"}, {"account": "CRM_102", "mobile": "13800138102", "name": "王五"}, {"account": "CRM_103", "mobile": "13800138103", "name": "赵六"}]

#     for member in members:
#         # 加密手机号
#         encrypted = cdp_client.encrypt_mobile_md5(member["mobile"])

#         # 扩展信息
#         extend = {"real_name": member["name"], "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

#         # 调用接口
#         result = cdp_client.member_reg_and_bind(account=member["account"], platform="JD", mix_mobile=encrypted, extend=extend)

#         print(f"会员 {member['account']} ({member['name']}) 处理结果: {result.get('code')} - {result.get('msg')}")

#         # 避免频繁调用，简单延时
#         time.sleep(0.5)
