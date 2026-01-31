# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2026-01-16 10:41:08
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class JdUserDataModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(JdUserDataModel, self).__init__(JdUserData, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类


class JdUserData:
    def __init__(self):
        super(JdUserData, self).__init__()
        self.id = 0
        self.business_id = 0  # 商家标识
        self.xid = ''  # 京东应用下用户唯一标识
        self.total_order_price = 0 # 累计订单金额
        self.total_order_count = 0  # 累计订单数量
        self.info_json = {}  # 扩展信息json
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间
        self.modify_date = '1970-01-01 00:00:00.000'  # 修改时间

    @classmethod
    def get_field_list(self):
        return ['id', 'business_id', 'xid', 'total_order_price', 'total_order_count', 'info_json', 'create_date', 'modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "jd_user_data_tb"
