from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_EFP_ACCTPAYMENT_REFUND



class V2EfpAcctpaymentRefundRequest(object):
    """
    全渠道资金付款到账户退款
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 原交易全局流水号org_hf_seq_id和org_req_seq_id二选一； &lt;font color&#x3D;&quot;green&quot;&gt;示例值：00470topo1A211015160805P090ac132fef00000&lt;/font&gt;
    org_hf_seq_id = ""
    # 原交易请求流水号org_hf_seq_id和org_req_seq_id二选一；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665002&lt;/font&gt;
    org_req_seq_id = ""
    # 原交易请求日期
    org_req_date = ""
    # 退款金额
    refund_amt = ""
    # 接收方退款对象
    acct_split_bunch = ""

    def post(self, extend_infos):
        """
        全渠道资金付款到账户退款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "org_hf_seq_id":self.org_hf_seq_id,
            "org_req_seq_id":self.org_req_seq_id,
            "org_req_date":self.org_req_date,
            "refund_amt":self.refund_amt,
            "acct_split_bunch":self.acct_split_bunch
        }
        required_params.update(extend_infos)
        return request_post(V2_EFP_ACCTPAYMENT_REFUND, required_params)
