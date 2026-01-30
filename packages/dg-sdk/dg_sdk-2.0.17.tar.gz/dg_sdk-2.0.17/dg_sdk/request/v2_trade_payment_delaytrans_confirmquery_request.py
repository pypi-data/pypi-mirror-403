from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_DELAYTRANS_CONFIRMQUERY



class V2TradePaymentDelaytransConfirmqueryRequest(object):
    """
    交易确认查询接口
    """

    # 原请求日期
    org_req_date = ""
    # 原请求流水号
    org_req_seq_id = ""
    # 商户号
    huifu_id = ""

    def post(self, extend_infos):
        """
        交易确认查询接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_DELAYTRANS_CONFIRMQUERY, required_params)
