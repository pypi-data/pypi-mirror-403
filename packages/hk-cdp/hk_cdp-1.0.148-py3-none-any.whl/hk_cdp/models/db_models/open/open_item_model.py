# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-11-22 17:10:05
@LastEditTime: 2026-01-27 14:08:21
@LastEditors: HuangJianYi
@Description: 
"""
#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class OpenItemModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(OpenItemModel, self).__init__(OpenItem, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类


class OpenItem:
    def __init__(self):
        super(OpenItem, self).__init__()
        self.id = 0 # ID
        self.goods_id = ""  # 商品ID
        self.store_id = ""  # 平台店铺标识
        self.cid = ""  # 分类ID
        self.goods_code = ""  # 商家编码
        self.goods_name = ""  # 商品名称
        self.goods_pic = ""  # 商品主图片
        self.approve_status = ""  # 商品状态
        self.price = 0.0000  # 商品价格
        self.goods_num = 0  # 商品件数
        self.is_delete = 0  # 是否删除
        self.info_json = {}  # 扩展信息
        self.skus = []  # sku列表
        self.create_date = "1970-01-01 00:00:00.000"  # 创建时间
        self.modify_date = "1970-01-01 00:00:00.000"  # 修改时间
        self.open_create_date = "1970-01-01 00:00:00.000"  # 开放平台创建时间
        self.open_modify_date = "1970-01-01 00:00:00.000"  # 开放平台修改时间


    @classmethod
    def get_field_list(self):
        return ['id', 'goods_id', 'store_id', 'cid', 'goods_code', 'goods_name', 'goods_pic', 'approve_status', 'price', 'goods_num', 'is_delete', 'info_json', 'skus', 'create_date', 'modify_date', 'open_create_date', 'open_modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "open_item_tb"
