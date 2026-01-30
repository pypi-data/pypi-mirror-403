from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_BANKPAY_BANKLIST



class V2TradeOnlinepaymentBankpayBanklistRequest(object):
    """
    网银支持银行列表查询
    """

    # 商户号
    huifu_id = ""
    # 网关支付类型
    gate_type = ""
    # 订单类型
    order_type = ""

    def post(self, extend_infos):
        """
        网银支持银行列表查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "gate_type":self.gate_type,
            "order_type":self.order_type
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_BANKPAY_BANKLIST, required_params)
