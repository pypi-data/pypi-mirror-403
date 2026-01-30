from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_ZXE_ACCTPYERQUERY



class V2TradePaymentZxeAcctpyerqueryRequest(object):
    """
    电子账户付款查询
    """

    # 商户号
    huifu_id = ""
    # 原交易请求日期
    org_req_date = ""
    # 原交易返回的全局流水号原交易请求流水号、原交易返回的全局流水号至少要送其中一项；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：00290TOP1GR210919004230P853ac13262200000&lt;/font&gt;
    org_hf_seq_id = ""
    # 原交易请求流水号原交易请求流水号、原交易返回的全局流水号至少要送其中一项；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665001&lt;/font&gt;
    org_req_seq_id = ""

    def post(self, extend_infos):
        """
        电子账户付款查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_hf_seq_id":self.org_hf_seq_id,
            "org_req_seq_id":self.org_req_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_ZXE_ACCTPYERQUERY, required_params)
