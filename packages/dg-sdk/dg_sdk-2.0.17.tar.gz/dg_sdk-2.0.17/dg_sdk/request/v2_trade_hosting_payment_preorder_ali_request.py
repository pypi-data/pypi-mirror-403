from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_HOSTING_PAYMENT_PREORDER



class V2TradeHostingPaymentPreorderAliRequest(object):
    """
    支付宝小程序预下单接口
    """

    # 商户号
    huifu_id = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 预下单类型
    pre_order_type = ""
    # 交易金额
    trans_amt = ""
    # 商品描述
    goods_desc = ""
    # app扩展参数集合
    app_data = ""

    def post(self, extend_infos):
        """
        支付宝小程序预下单接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "pre_order_type":self.pre_order_type,
            "trans_amt":self.trans_amt,
            "goods_desc":self.goods_desc,
            "app_data":self.app_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_HOSTING_PAYMENT_PREORDER, required_params)
