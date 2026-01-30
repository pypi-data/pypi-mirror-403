from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ACCTPAYMENT_REFUND



class V2TradeAcctpaymentRefundRequest(object):
    """
    余额支付退款
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 原余额支付请求日期
    org_req_date = ""
    # 原余额支付请求流水号org_hf_seq_id和orgReqSeqId二选一；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665001&lt;/font&gt;
    org_req_seq_id = ""
    # 原余额支付支付全局流水号org_hf_seq_id和orgReqSeqId二选一；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：00470topo1A211015160805P090ac132fef00000&lt;/font&gt;
    org_hf_seq_id = ""
    # 退款金额
    ord_amt = ""

    def post(self, extend_infos):
        """
        余额支付退款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "org_hf_seq_id":self.org_hf_seq_id,
            "ord_amt":self.ord_amt
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ACCTPAYMENT_REFUND, required_params)
