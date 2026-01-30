from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYSCORE_SERVICEORDER_CANCEL



class V2TradePayscoreServiceorderCancelRequest(object):
    """
    取消支付分订单
    """

    # 汇付商户号
    huifu_id = ""
    # 取消服务订单原因
    reason = ""

    def post(self, extend_infos):
        """
        取消支付分订单

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "reason":self.reason
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYSCORE_SERVICEORDER_CANCEL, required_params)
