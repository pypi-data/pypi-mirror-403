# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2025-01-09 17:57:48
@LastEditTime: 2026-01-26 16:51:51
@LastEditors: HuangJianYi
@Description: 
"""


class ListKey():
    """
    @description: 队列key
    """
    @classmethod
    def tt_history_member_list(self, store_id, is_check=False):
        """
        :description: 抖音历史会员队列（每个抖音店铺，第一次对接的时候使用一次性同步历史会员数据）
        :param store_id: 店铺标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "tt_history_member_list"
        if is_check == True:
            return f"{prefix}:check:{store_id}"
        return f"{prefix}:{store_id}"

    @classmethod
    def member_merge_list(self, merge_type, store_id, is_check=False):
        """
        :description: one_id合并队列
        :param merge_type: 合并类型，'omid' 或 'telephone'
        :param store_id: 店铺标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = f"member_{merge_type}_merge_list"
        if is_check == True:
            return f"{prefix}:check:{store_id}"
        return f"{prefix}:{store_id}"

    @classmethod
    def register_member_list(self, store_id, is_check=False):
        """
        :description: 注册增量会员进行初始化计算队列
        :param store_id: 店铺标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "register_member_list"
        if is_check == True:
            return f"{prefix}:check:{store_id}"
        return f"{prefix}:{store_id}"

    @classmethod
    def history_member_list(self, store_id, is_check=False):
        """
        :description: 历史老会员进行初始化计算队列
        :param store_id: 店铺标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "history_member_list"
        if is_check == True:
            return f"{prefix}:check:{store_id}"
        return f"{prefix}:{store_id}"

    @classmethod
    def member_mask_telephone_list(self, business_id, is_check=False):
        """
        :description: 掩码手机号处理队列（通过其他平台的手机码去抖音匹配，让抖音的会员得到真实的手机号）
        :param business_id: 商家标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "member_mask_telephone_list"
        if is_check == True:
            return f"{prefix}:check:businessid_{business_id}"
        return f"{prefix}:businessid_{business_id}"

    @classmethod
    def member_sync_list(self, business_id, is_check=False):
        """
        :description: 会员同步队列
        :param business_id: 商家标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "member_sync_list"
        if is_check == True:
            return f"{prefix}:check:businessid_{business_id}"
        return f"{prefix}:businessid_{business_id}"

    @classmethod
    def member_point_change_sync_list(self, business_id, is_check=False):
        """
        :description: 会员积分变更同步队列
        :param business_id: 商家标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "member_point_change_sync_list"
        if is_check == True:
            return f"{prefix}:check:businessid_{business_id}"
        return f"{prefix}:businessid_{business_id}"

    @classmethod
    def point_change_callback_list(self, business_id, is_check=False):
        """
        :description: 线下品牌积分变更消息回调API，告诉积分扣减或者累加是否成功。 
        :param business_id: 商家标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "point_change_callback_list"
        if is_check == True:
            return f"{prefix}:check:businessid_{business_id}"
        return f"{prefix}:businessid_{business_id}"

    @classmethod
    def member_info_update_list(self, business_id, is_check=False):
        """
        :description: 品牌会员入会时多店铺会员信息补充
        :param business_id: 商家标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "member_info_update_list"
        if is_check == True:
            return f"{prefix}:check:businessid_{business_id}"
        return f"{prefix}:businessid_{business_id}"

    @classmethod
    def jd_pull_integral_list(self, store_id, is_check=False):
        """
        :description: 京东拉取积分队列
        :param store_id: 店铺标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "jd_pull_integral_list"
        if is_check == True:
            return f"{prefix}:check:{store_id}"
        return f"{prefix}:{store_id}"

    @classmethod
    def jd_push_integral_confirm_list(self, store_id, is_check=False):
        """
        :description: 京东确认积分队列
        :param store_id: 店铺标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "jd_confirm_push_integral_list"
        if is_check == True:
            return f"{prefix}:check:{store_id}"
        return f"{prefix}:{store_id}"

    @classmethod
    def jd_domain_member_list(self, store_id, is_check=False):
        """
        :description: 全域会员结算队列
        :param store_id: 店铺标识
        :param is_check: is_check
        :return str
        :last_editors: HuangJianYi
        """
        prefix = "jd_domain_member_list"
        if is_check == True:
            return f"{prefix}:check:{store_id}"
        return f"{prefix}:{store_id}"


class CacheKey():
    """
    @description: 缓存key
    """
    @classmethod
    def cdp_work_info(self, work_name, store_id=None):
        """
        :description: CDP作业信息
        :param store_id: 店铺标识
        :param work_name: 作业名称(对应函数名)
        :return str
        :last_editors: HuangJianYi
        """
        dependency_key = f"cdp_work_info:workname_{work_name}"
        if store_id:
            dependency_key += f"_storeid_{store_id}"
        return dependency_key

    @classmethod
    def member_info(self, one_id):
        """
        :description: 会员信息
        :param one_id: one_id
        :return str
        :last_editors: HuangJianYi
        """
        dependency_key = f"member_info:oneid_{one_id}"
        return dependency_key

    @classmethod
    def user_info(self, ouid, plat_store_id):
        """
        :description: 用户信息
        :param ouid: ouid
        :param plat_store_id: 店铺ID
        :return str
        :last_editors: HuangJianYi
        """
        dependency_key = f"user_info:ouid_{ouid}_platstoreid_{plat_store_id}"
        return dependency_key

    @classmethod
    def user_info_by_userid(self, user_id):
        """
        :description: 用户信息
        :param user_id：用户标识
        :return str
        :last_editors: HuangJianYi
        """
        return f"user_info:userid_{user_id}"

    @classmethod
    def member_asset(self, one_id):
        """
        :description: 会员资产
        :param one_id：one_id
        :return str
        :last_editors: HuangJianYi
        """
        return f"member_asset:oneid_{one_id}"

    @classmethod
    def store_base(self, store_id):
        """
        :description: 用户信息
        :param user_id：用户标识
        :return str
        :last_editors: HuangJianYi
        """
        return f"store_base:storeid_{store_id}"

    @classmethod
    def business_info(self, business_id):
        """
        :description: 商家信息
        :param business_id：商家标识
        :return str
        :last_editors: HuangJianYi
        """
        return f"business_info:businessid_{business_id}"

    @classmethod
    def scheme_level_info(self, scheme_id, level_id=None):
        """
        :description: 等级信息
        :param scheme_id：体系标识
        :param level_id：等级标识
        :return str
        :last_editors: HuangJianYi
        """
        dependency_key = f"scheme_level_info:schemeid_{scheme_id}"
        if level_id:
            dependency_key = dependency_key + f"_levelid_{level_id}"
        return dependency_key

    @classmethod
    def scheme_level(self, scheme_id):
        """
        :description: 体系等级配置
        :param scheme_id：体系标识
        :return str
        :last_editors: HuangJianYi
        """
        return f"scheme_level:schemeid_{scheme_id}"

    @classmethod
    def scheme_integral(self, scheme_id):
        """
        :description: 体系积分配置
        :param scheme_id：体系标识
        :return str
        :last_editors: HuangJianYi
        """
        return f"scheme_integral:schemeid_{scheme_id}"

    @classmethod
    def scheme_growth(self, scheme_id):
        """
        :description: 体系成长值配置
        :param scheme_id：体系标识
        :return str
        :last_editors: HuangJianYi
        """
        return f"scheme_growth:schemeid_{scheme_id}"
