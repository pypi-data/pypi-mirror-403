from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ACCTPAYMENT_REFUND_QUERY



class V2TradeAcctpaymentRefundQueryRequest(object):
    """
    余额支付退款查询
    """

    # 退款请求流水号
    org_req_seq_id = ""
    # 余额支付退款请求日期
    org_req_date = ""
    # 商户号
    huifu_id = ""

    def post(self, extend_infos):
        """
        余额支付退款查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "org_req_seq_id":self.org_req_seq_id,
            "org_req_date":self.org_req_date,
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ACCTPAYMENT_REFUND_QUERY, required_params)
