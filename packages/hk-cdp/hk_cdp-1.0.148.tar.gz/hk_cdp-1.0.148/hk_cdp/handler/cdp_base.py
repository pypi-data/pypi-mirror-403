# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-12-13 11:45:32
@LastEditTime: 2026-01-28 14:58:21
@LastEditors: HuangJianYi
@Description: 
"""
from seven_cloudapp_frame.handlers.frame_base import *
from seven_cloudapp_frame.libs.customize.seven_helper import *
from hk_cdp.models.cdp_model import *


class TiktokSpiBaseHandler(FrameBaseHandler):
    """
    :description: TikTok SPI基础处理类
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def response_json_success(self, data=None, desc='success'):
        """
        :Description: 通用成功返回json结构
        :param desc: 返回结果描述
        :param data: 返回结果对象，即为数组，字典
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        return self.response_common(0, desc, data, {"is_success": 1})

    def response_json_error(self, code=200007, desc='系统服务错误或者异常，请稍后重试', data=None):
        """
        :Description: 通用错误返回json结构
        :param desc: 错误描述
        :param data: 错误编码
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        return self.response_common(code, desc, data, {"is_success": 0})

    def response_json_error_params(self, desc='params error'):
        """
        :Description: 通用参数错误返回json结构
        :param desc: 返错误描述
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        return self.response_common(1, desc)

    def response_common(self, code, desc="", data=None, log_extra_dict=None):
        """
        :Description: 输出公共json模型
        :param code: 返回结果标识
        :param desc: 返回结果描述
        :param data: 返回结果对象，即为数组，字典
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        if hasattr(data, '__dict__'):
            data = data.__dict__

        rep_dic = {}
        rep_dic['code'] = code
        rep_dic['message'] = desc
        rep_dic['data'] = data

        return self.http_response(SevenHelper.json_dumps(rep_dic), log_extra_dict)

    def response_json_error_sign(self):
        """
        :Description: 签名验证失败错误返回json结构
        :param desc: 返错误描述
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        return self.response_common(100001, '签名验证失败', None, {"is_success": 0})


class JdSpiBaseHandler(FrameBaseHandler):
    """
    :description: 京东 SPI基础处理类
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def response_json_success(self, data=None, desc='调用成功'):
        """
        :Description: 通用成功返回json结构
        :param desc: 返回结果描述
        :param data: 返回结果对象，即为数组，字典
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        return self.response_common("0", desc, data, {"is_success": 1})

    def response_json_error(self, code='999999', desc='调用失败，未知错误', data=None):
        """
        :Description: 通用错误返回json结构
        :param desc: 错误描述
        :param data: 错误编码
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        return self.response_common(code, desc, data, {"is_success": 0})

    def response_json_error_params(self, desc='参数缺失，缺少必填参数'):
        """
        :Description: 通用参数错误返回json结构
        :param desc: 返错误描述
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        return self.response_common("9001", desc)

    def response_common(self, code, desc="", data=None, log_extra_dict=None):
        """
        :Description: 输出公共json模型
        :param code: 返回结果标识
        :param desc: 返回结果描述
        :param data: 返回结果对象，即为数组，字典
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        if hasattr(data, '__dict__'):
            data = data.__dict__

        rep_dic = {}
        rep_dic['code'] = code
        rep_dic['msg'] = desc
        rep_dic['data'] = data

        return self.http_response(SevenHelper.json_dumps(rep_dic), log_extra_dict)

    def response_json_error_sign(self):
        """
        :Description: 签名验证失败错误返回json结构
        :param desc: 返错误描述
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJianYi
        """
        return self.response_common("9003", '无效的 token', None, {"is_success": 0})

    def check_params(self, must_array):
        """
        :Description: 必传参数校验
        :param must_array: 必传参数数组
        :return: True-缺少必传参数 False-参数齐全
        :last_editors: HuangJianYi
        """
        if isinstance(must_array, str):
            must_array = must_array.split(',')
        for must_param in must_array:
            if must_param not in self.request_params or self.request_params[must_param] == "":
                return True
        return False

    def get_business_store_info(self, brand_id):
        """
        :description: 获取商家店铺信息（redis缓存）
        :param brand_id: 对应京东的体系ID                
        :return: invoke_result_data
        :last_editors: WangQiang
        """
        from hk_cdp.models.db_models.cap.cap_business_info_model import CapBusinessInfoModel
        from hk_cdp.models.db_models.store.store_base_model import StoreBaseModel
        from hk_cdp.models.db_models.cdp.cdp_store_info_model import CdpStoreInfoModel

        invoke_result_data = InvokeResultData()
        redis_init = SevenHelper.redis_init()
        business_store_key = f"business_store_info:brandid_{brand_id}_platform_3"
        redis_data = redis_init.get(business_store_key)
        if not redis_data:
            cdp_store_info_model = CdpStoreInfoModel(context=self)
            # 查询CDP店铺表
            store_info_dict = cdp_store_info_model.get_cache_dict(where="plat_object_id=%s and platform_id=3", order_by="id asc", field="id,guid,seller_nick,store_name,plat_store_id,business_id,extend_info,plat_telephone_key", params=[brand_id])
            if not store_info_dict:
                invoke_result_data.success = False
                invoke_result_data.error_code = "no_store_info"
                invoke_result_data.error_message = "找不到店铺信息"
                return invoke_result_data
            # 查询商家信息
            cap_business_info_model = CapBusinessInfoModel(context=self)
            business_info_dict = cap_business_info_model.get_cache_dict_by_id(store_info_dict["business_id"], field="id,guid,business_code,extend_info")
            if not business_info_dict:
                invoke_result_data.success = False
                invoke_result_data.error_code = "no_business_info"
                invoke_result_data.error_message = "找不到商家信息"
                return invoke_result_data
            db_config = SevenHelper.json_loads(business_info_dict["extend_info"]).get("cdp_db_config", {})
            business_info_dict["cdp_db_config"] = db_config
            # 查询店铺信息
            store_base_model = StoreBaseModel(context=self, db_config_dict=db_config)
            store_base_dict = store_base_model.get_cache_dict_by_id(primary_key_id=store_info_dict["id"], field="id,scheme_id,is_omid_merge,incr_process_start_date")
            if not store_base_dict:
                invoke_result_data.success = False
                invoke_result_data.error_code = "no_store_base"
                invoke_result_data.error_message = "找不到店铺基础信息"
                return invoke_result_data
            store_info_dict.update(store_base_dict)
            redis_data = {}
            redis_data["store_base_dict"] = store_info_dict
            redis_data["business_info_dict"] = business_info_dict
            redis_init.set(name=business_store_key, value=SevenHelper.json_dumps(redis_data), ex=600)
        else:
            redis_data = SevenHelper.json_loads(redis_data)
        invoke_result_data.data = redis_data
        return invoke_result_data


class OpenBaseHandler(FrameBaseHandler):
    """
    :description: 开放平台基础处理类
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_app_id(self):
        """     
        :Description: 获取应用ID
        :return: app_id
        :last_editors: HuangJianYi
        """
        app_id = ''
        app_info = self.request.headers._dict.get("X-App-Info")
        if app_info:
            app_info_dict = self.json_loads(app_info)
            if app_info_dict and 'app_id' in app_info_dict:
                app_id = app_info_dict['app_id']
        return app_id

    def business_process_executing(self):
        """     
        :Description: 必传参数校验
        :param must_array: 必传参数数组
        :return: True-缺少必传参数 False-参数齐全
        :last_editors: HuangJianYi
        """
        from hk_cdp.models.db_models.cap.cap_business_info_model import CapBusinessInfoModel
        from hk_cdp.models.db_models.store.store_base_model import StoreBaseModel
        from hk_cdp.models.db_models.cdp.cdp_store_info_model import CdpStoreInfoModel

        invoke_result_data = InvokeResultData()
        business_id = self.request.headers._dict.get("X-Consumer-Custom-Id")
        if not business_id:
            invoke_result_data.success = False
            invoke_result_data.error_code = "param_error"
            invoke_result_data.error_message = "缺少必要参数Business_id"
            return invoke_result_data
        app_info = self.request.headers._dict.get("X-App-Info")
        if not app_info:
            invoke_result_data.success = False
            invoke_result_data.error_code = "param_error"
            invoke_result_data.error_message = "缺少必要参数App-Info"
            return invoke_result_data
        app_info_dict = self.json_loads(app_info)
        if not app_info_dict or 'store_id' not in app_info_dict:
            invoke_result_data.success = False
            invoke_result_data.error_code = "param_error"
            invoke_result_data.error_message = "缺少必要参数store_id"
            return invoke_result_data
        store_id = app_info_dict['store_id']
        cap_business_info_model = CapBusinessInfoModel(context=self)
        business_info_dict = cap_business_info_model.get_cache_dict_by_id(int(business_id), field="id,business_code,extend_info", dependency_key=CacheKey.business_info(business_id))
        if not business_info_dict or not business_info_dict["extend_info"]:
            invoke_result_data.success = False
            invoke_result_data.error_code = "business_error"
            invoke_result_data.error_message = "找不到商家信息"
            return invoke_result_data
        business_info_dict["extend_info"] = SevenHelper.json_loads(business_info_dict["extend_info"])
        cdp_db_config = business_info_dict["extend_info"].get("cdp_db_config")
        if not cdp_db_config:
            invoke_result_data.success = False
            invoke_result_data.error_code = "business_error"
            invoke_result_data.error_message = "商家信息不完整"
            return invoke_result_data
        store_base_model = StoreBaseModel(db_config_dict=cdp_db_config, context=self)
        store_base_dict = store_base_model.get_cache_dict("id=%s", field="*", params=[store_id], dependency_key=CacheKey.store_base(store_id))
        if not store_base_dict:
            invoke_result_data.success = False
            invoke_result_data.error_code = "store_error"
            invoke_result_data.error_message = "找不到店铺基础信息"
            return invoke_result_data
        if store_base_dict['scheme_id'] == 0:
            invoke_result_data.success = False
            invoke_result_data.error_code = "store_error"
            invoke_result_data.error_message = "店铺未绑定会员体系"
            return invoke_result_data
        invoke_result_data.data = {"store_base_dict": store_base_dict, "cdp_db_config": cdp_db_config, "business_info_dict": business_info_dict, "app_info_dict": app_info_dict}
        return invoke_result_data
