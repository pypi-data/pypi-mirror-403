# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2026-01-30 13:48:27
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class JdMemberSyncModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(JdMemberSyncModel, self).__init__(JdMemberSync, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类


class JdMemberSync:
    def __init__(self):
        super(JdMemberSync, self).__init__()
        self.id = 0  # id
        self.business_id = 0  # 商家标识
        self.scheme_id = 0  # 会员体系标识
        self.member_telephone = ''  # 会员手机号
        self.user_id = ''  # 客户ID
        self.data_type = 0  # 数据类型（1-上行 1-下行）
        self.member_type = 0  # 会员类型(1- 一方 2-全域 3-仅京东)
        self.bind_status = 0  # 绑定状态(0-只有一方注册 1-只有京东会员通注册 2-已匹配  3- 一方与京东会员通都解绑)
        self.business_type = 0  # 业务类型(0-初始 1-增量)
        self.parent_user_id = ''  # 父客户ID
        self.sync_integral = 0  # 同步积分
        self.sync_status = 0  # 同步状态(0-未同步 1-已同步 2-同步中  3-不予同步)
        self.sync_count = 0  # 同步次数
        self.sync_result = ''  # 同步结果
        self.sync_date = '1970-01-01 00:00:00.000'  # 同步时间
        self.info_json = {}  # 扩展信息json
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间
        self.modify_date = '1970-01-01 00:00:00.000'  # 修改时间

    @classmethod
    def get_field_list(self):
        return ['id', 'business_id', 'scheme_id', 'member_telephone', 'user_id', 'data_type', 'member_type', 'bind_status', 'business_type', 'parent_user_id', 'sync_integral', 'sync_status', 'sync_count', 'sync_result', 'sync_date', 'info_json', 'create_date', 'modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "jd_member_sync_tb"
