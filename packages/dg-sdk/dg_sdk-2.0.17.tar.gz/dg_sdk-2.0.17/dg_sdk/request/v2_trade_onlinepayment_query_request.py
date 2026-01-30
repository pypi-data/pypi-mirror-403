from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_QUERY



class V2TradeOnlinepaymentQueryRequest(object):
    """
    线上交易查询
    """

    # 商户号
    huifu_id = ""
    # 原交易请求日期
    org_req_date = ""
    # 原交易返回的全局流水号原交易请求流水号、原交易返回的全局流水号至少要送其中一项；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：00290TOP1GR210919004230P853ac13262200000&lt;/font&gt;
    org_hf_seq_id = ""
    # 原交易请求流水号原交易请求流水号、原交易返回的全局流水号至少要送其中一项；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665001&lt;/font&gt;
    org_req_seq_id = ""
    # 原交易支付类型QUICK_PAY：快捷支付、快捷充值(查询快捷交易必填)&lt;br/&gt;ONLINE_PAY：网银支付、网银充值&lt;br/&gt;WAP_PAY：手机WAP支付&lt;br/&gt;UNION_PAY：银联APP统一支付&lt;br/&gt;QUICK_PAY_APPLY：银行卡分期申请&lt;br/&gt;QUICK_PAY_CONFIRM：银行卡分期确认&lt;br/&gt;TRANSFER_ACCT：网银转账&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：TRANSFER_ACCT&lt;/font&gt;&lt;br/&gt;注意：**不支持聚合扫码接口生成的微信、支付宝、银联二维码等交易的查询。**
    pay_type = ""

    def post(self, extend_infos):
        """
        线上交易查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_hf_seq_id":self.org_hf_seq_id,
            "org_req_seq_id":self.org_req_seq_id,
            "pay_type":self.pay_type
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_QUERY, required_params)
