from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYSCORE_SERVICEORDER_QUERY



class V2TradePayscoreServiceorderQueryRequest(object):
    """
    查询支付分订单
    """

    # 汇付商户号
    huifu_id = ""

    def post(self, extend_infos):
        """
        查询支付分订单

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYSCORE_SERVICEORDER_QUERY, required_params)
