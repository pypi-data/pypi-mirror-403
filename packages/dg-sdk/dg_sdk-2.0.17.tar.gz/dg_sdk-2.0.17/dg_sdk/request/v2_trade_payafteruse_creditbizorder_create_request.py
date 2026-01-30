from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYAFTERUSE_CREDITBIZORDER_CREATE



class V2TradePayafteruseCreditbizorderCreateRequest(object):
    """
    服务单创建
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 订单总金额
    trans_amt = ""
    # 支付宝用户ID
    buyer_id = ""
    # 订单标题
    title = ""
    # 订单类型
    merchant_biz_type = ""
    # 订单详情地址
    path = ""
    # 芝麻信用服务ID
    zm_service_id = ""
    # 商品详细信息
    item_infos = ""

    def post(self, extend_infos):
        """
        服务单创建

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "trans_amt":self.trans_amt,
            "buyer_id":self.buyer_id,
            "title":self.title,
            "merchant_biz_type":self.merchant_biz_type,
            "path":self.path,
            "zm_service_id":self.zm_service_id,
            "item_infos":self.item_infos
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYAFTERUSE_CREDITBIZORDER_CREATE, required_params)
