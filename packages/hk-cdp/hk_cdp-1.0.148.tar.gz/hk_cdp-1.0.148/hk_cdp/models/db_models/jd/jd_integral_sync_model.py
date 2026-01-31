# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2026-01-20 17:12:20
@LastEditTime: 2026-01-30 13:52:49
@LastEditors: HuangJianYi
@Description: 
"""

from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class JdIntegralSyncModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(JdIntegralSyncModel, self).__init__(JdIntegralSync, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类


class JdIntegralSync:
    def __init__(self):
        super(JdIntegralSync, self).__init__()
        self.id = 0  # id
        self.business_id = 0  # 商家标识
        self.scheme_id = 0  # 会员体系标识
        self.user_id = ''  # 客户ID
        self.log_title = ''  # 标题
        self.operate_type = 0  # 变更类型 （0-增加 1-扣减）
        self.operate_value = 0  # 操作值
        self.sync_status = 0  # 同步状态(0-未同步 1-已同步 2-同步中  3-不予同步)
        self.sync_count = 0  # 同步次数
        self.sync_result = ''  # 同步结果
        self.sync_date = '1970-01-01 00:00:00.000'  # 同步时间
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间
        self.modify_date = '1970-01-01 00:00:00.000'  # 修改时间

    @classmethod
    def get_field_list(self):
        return ['id', 'business_id', 'scheme_id', 'user_id', 'log_title', 'operate_type', 'operate_value', 'sync_status', 'sync_count', 'sync_result', 'sync_date', 'create_date', 'modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "jd_integral_sync_tb"
