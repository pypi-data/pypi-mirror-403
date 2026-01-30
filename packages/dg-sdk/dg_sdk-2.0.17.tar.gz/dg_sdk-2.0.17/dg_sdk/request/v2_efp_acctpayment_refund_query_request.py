from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_EFP_ACCTPAYMENT_REFUND_QUERY



class V2EfpAcctpaymentRefundQueryRequest(object):
    """
    全渠道资金付款到账户退款查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 退款交易请求流水号
    org_req_seq_id = ""
    # 退款交易请求日期
    org_req_date = ""

    def post(self, extend_infos):
        """
        全渠道资金付款到账户退款查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "org_req_seq_id":self.org_req_seq_id,
            "org_req_date":self.org_req_date
        }
        required_params.update(extend_infos)
        return request_post(V2_EFP_ACCTPAYMENT_REFUND_QUERY, required_params)
