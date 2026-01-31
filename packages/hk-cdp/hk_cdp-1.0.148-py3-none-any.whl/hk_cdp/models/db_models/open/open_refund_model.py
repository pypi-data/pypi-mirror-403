#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class OpenRefundModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(OpenRefundModel, self).__init__(OpenRefund, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类


class OpenRefund:
    def __init__(self):
        super(OpenRefund, self).__init__()
        self.id = 0 # ID
        self.refund_id = ''  # 退款号
        self.store_id = ""  # 平台店铺标识
        self.main_order_id = ''  # 主订单号
        self.sub_order_id = '' # 子订单号
        self.goods_id = ""  # 商品ID
        self.sku_id = ""  # 买家昵称
        self.refund_status = ""  # 状态
        self.refund_price = 0.0000  # 退款金额
        self.refund_reason = ""  # 退款原因
        self.info_json = {}  # 扩展信息
        self.create_date = "1970-01-01 00:00:00.000"  # 创建时间
        self.modify_date = "1970-01-01 00:00:00.000"  # 修改时间
        self.open_create_date = "1970-01-01 00:00:00.000"  # 开放平台创建时间
        self.open_modify_date = "1970-01-01 00:00:00.000"  # 开放平台修改时间

    @classmethod
    def get_field_list(self):
        return ['id', 'refund_id', 'store_id', 'main_order_id', 'sub_order_id', 'goods_id', 'sku_id', 'refund_status', 'refund_price', 'refund_reason', 'info_json', 'create_date', 'modify_date', 'open_create_date', 'open_modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "open_refund_tb"
