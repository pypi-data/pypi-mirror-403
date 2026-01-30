from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_REFUND_QUERY



class V2TradeOnlinepaymentRefundQueryRequest(object):
    """
    线上交易退款查询
    """

    # 商户号
    huifu_id = ""
    # 原退款请求日期
    org_req_date = ""

    def post(self, extend_infos):
        """
        线上交易退款查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_REFUND_QUERY, required_params)
