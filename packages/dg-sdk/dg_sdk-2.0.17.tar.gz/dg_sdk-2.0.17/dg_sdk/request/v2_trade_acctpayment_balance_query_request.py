from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ACCTPAYMENT_BALANCE_QUERY



class V2TradeAcctpaymentBalanceQueryRequest(object):
    """
    账户余额信息查询
    """

    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""

    def post(self, extend_infos):
        """
        账户余额信息查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ACCTPAYMENT_BALANCE_QUERY, required_params)
