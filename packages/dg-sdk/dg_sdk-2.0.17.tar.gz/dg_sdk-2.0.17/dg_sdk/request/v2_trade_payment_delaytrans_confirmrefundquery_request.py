from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_DELAYTRANS_CONFIRMREFUNDQUERY



class V2TradePaymentDelaytransConfirmrefundqueryRequest(object):
    """
    交易确认退款查询
    """

    # 商户号
    huifu_id = ""
    # 原交易请求日期
    org_req_date = ""
    # 原交易请求流水号指交易确认退款请求流水号，org_req_seq_id和org_hf_seq_id二选一；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665002&lt;/font&gt;
    org_req_seq_id = ""
    # 原退款全局流水号原交易确认退款全局流水号。org_req_seq_id和org_hf_seq_id二选一；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：003500TOP2B211021163242P447ac132fd200000&lt;/font&gt;
    org_hf_seq_id = ""

    def post(self, extend_infos):
        """
        交易确认退款查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "org_hf_seq_id":self.org_hf_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_DELAYTRANS_CONFIRMREFUNDQUERY, required_params)
