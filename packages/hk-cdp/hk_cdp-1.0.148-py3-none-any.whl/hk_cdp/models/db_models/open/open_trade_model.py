# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2026-01-27 13:40:18
@LastEditTime: 2026-01-27 14:13:53
@LastEditors: HuangJianYi
@Description: 
"""
#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class OpenTradeModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(OpenTradeModel, self).__init__(OpenTrade, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类


class OpenTrade:
    def __init__(self):
        super(OpenTrade, self).__init__()
        self.id = 0 # ID
        self.main_order_id = ""  # 订单ID
        self.ouid = ""  # 渠道用户唯一标识
        self.store_id = ""  # 店铺ID
        self.trade_type = ""  # 交易类型(fixed 普通订单（一口价）、step 团购订单 (包括预售订单)、nopaid 无付款订单(包括积分兑礼、抽奖赠送)、cod 货到付款、ec 电子凭证订单（虚拟物品订单）、other 其他类型)
        self.buy_num = 0  # 商品件数
        self.buyer_rate = 0  # 买家是否已评价(0-未评价 1-已评价)
        self.buyer_remark = ""  # 买家备注
        self.discount_price = 0.0000  # 优惠金额(单位：元)
        self.order_num = 0  # 子订单数
        self.order_price = 0.0000  # 订单金额(单位：元)
        self.order_status = ""  # 订单状态，(WAIT_BUYER_PAY 等待买家付款、SELLER_CONSIGNED_PART 卖家部分发货、WAIT_SELLER_SEND_GOODS 等待卖家发货,即:买家已付款、WAIT_BUYER_CONFIRM_GOODS 等待买家确认收货,即:卖家已发货、TRADE_BUYER_SIGNED 买家已签收,货到付款专用、TRADE_FINISHED 交易成功、TRADE_CLOSED 付款以后用户退款成功，交易自动关闭、TRADE_CANCEL 付款以前，卖家或买家主动关闭交易、BUYER_PART_PAY 买家部分支付)
        self.orders = []  # 订单列表
        self.pay_price = 0.0000  # 应付金额，等于子订单应付金额的累计值+邮费
        self.postage = 0.0000  # 邮费(单位：元)
        self.presale_status = ""  # 预售状态，预售订单需要传(FRONT_NOPAID_FINAL_NOPAID 定金未付尾款未付、FRONT_PAID_FINAL_NOPAID 定金已付尾款未付、FRONT_PAID_FINAL_PAID 定金和尾款都付)
        self.telephone = ""  # 收货人手机号
        self.receiver = ""  # 收货人
        self.receiver_address = ""  # 收货人所在地址
        self.receiver_city = ""  # 收货人所在城市
        self.receiver_county = ""  # 收货人所在城区
        self.receiver_province = ""  # 收货人所在省份
        self.trade_source_types = ""  # 交易内部来源（一笔订单可能同时有以上多个标记，则以逗号分隔）
        self.seller_rate = 0  # 卖家是否已评价(0-未评价 1-已评价)
        self.seller_remark = ""  # 卖家备注
        self.info_json = {}  # 扩展信息
        self.consign_date = "1970-01-01 00:00:00.000"  # 发货时间（yyyy-MM-dd HH:mm:ss）
        self.end_date = "1970-01-01 00:00:00.000"  # 交易结束时间（yyyy-MM-dd HH:mm:ss）。交易成功时间(更新交易状态为成功的同时更新)/确认收货时间或者交易关闭时间
        self.pay_date = "1970-01-01 00:00:00.000"  # 付款时间（yyyy-MM-dd HH:mm:ss）
        self.create_date = "1970-01-01 00:00:00.000"  # 下单时间（yyyy-MM-dd HH:mm:ss）
        self.modify_date = "1970-01-01 00:00:00.000"  # 修改时间（yyyy-MM-dd HH:mm:ss）
        self.open_create_date = "1970-01-01 00:00:00.000"  # 开放平台创建时间
        self.open_modify_date = "1970-01-01 00:00:00.000"  # 开放平台修改时间


    @classmethod
    def get_field_list(self):
        return ['id', 'main_order_id', 'ouid', 'store_id', 'trade_type', 'buy_num', 'buyer_rate', 'buyer_remark', 'consign_date', 'discount_price', 'end_date', 'order_num', 'order_price', 'order_status', 'orders', 'pay_price', 'postage', 'presale_status', 'telephone', 'receiver', 'receiver_address', 'receiver_city', 'receiver_county', 'receiver_province', 'trade_source_types', 'seller_rate', 'seller_remark', 'info_json', 'pay_date', 'create_date', 'modify_date', 'open_create_date', 'open_modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "open_trade_tb"
