from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_HOSTING_PAYMENT_QUERYORDERINFO



class V2TradeHostingPaymentQueryorderinfoRequest(object):
    """
    托管交易查询
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号开户自动生成；商户号不填时必填party_order_id；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：6666000123123123&lt;/font&gt;
    huifu_id = ""
    # 原交易请求日期请求格式：yyyyMMdd；该字段不填时必填party_order_id；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20221023&lt;/font&gt;
    org_req_date = ""
    # 原交易请求流水号该字段不填时必填party_order_id；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：rQ2021121311173944&lt;/font&gt;
    org_req_seq_id = ""
    # 用户账单上的商户订单号该字段不填时，商户号、原交易请求日期、原交易请求流水号必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：03232109190255105603561&lt;/font&gt;
    party_order_id = ""

    def post(self, extend_infos):
        """
        托管交易查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "party_order_id":self.party_order_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_HOSTING_PAYMENT_QUERYORDERINFO, required_params)
