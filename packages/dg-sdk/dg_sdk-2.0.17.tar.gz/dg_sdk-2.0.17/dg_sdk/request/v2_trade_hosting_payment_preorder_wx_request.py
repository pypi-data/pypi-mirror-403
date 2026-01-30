from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_HOSTING_PAYMENT_PREORDER



class V2TradeHostingPaymentPreorderWxRequest(object):
    """
    微信小程序预下单接口
    """

    # 预下单类型
    pre_order_type = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号
    huifu_id = ""
    # 交易金额
    trans_amt = ""
    # 商品描述
    goods_desc = ""
    # 微信小程序扩展参数集合
    miniapp_data = ""

    def post(self, extend_infos):
        """
        微信小程序预下单接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "pre_order_type":self.pre_order_type,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "trans_amt":self.trans_amt,
            "goods_desc":self.goods_desc,
            "miniapp_data":self.miniapp_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_HOSTING_PAYMENT_PREORDER, required_params)
