from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYSCORE_SERVICEORDER_COMPLETE



class V2TradePayscoreServiceorderCompleteRequest(object):
    """
    完结支付分订单
    """

    # 汇付商户号
    huifu_id = ""
    # 汇付订单号
    out_order_no = ""
    # 完结金额
    ord_amt = ""
    # 服务时间
    time_range = ""

    def post(self, extend_infos):
        """
        完结支付分订单

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "out_order_no":self.out_order_no,
            "ord_amt":self.ord_amt,
            "time_range":self.time_range
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYSCORE_SERVICEORDER_COMPLETE, required_params)
