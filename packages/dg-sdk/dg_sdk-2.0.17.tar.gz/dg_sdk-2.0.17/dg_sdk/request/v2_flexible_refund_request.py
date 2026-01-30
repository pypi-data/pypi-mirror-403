from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_FLEXIBLE_REFUND



class V2FlexibleRefundRequest(object):
    """
    灵工支付退款
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 原请求日期
    org_req_date = ""
    # 原灵工支付交易流水号&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665231&lt;/font&gt;
    org_req_seq_id = ""
    # 原灵工支付汇付全局流水号与原灵工支付交易流水号必选其一&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665001&lt;/font&gt;
    org_hf_seq_id = ""
    # 发起方商户号
    huifu_id = ""
    # 支付金额
    ord_amt = ""

    def post(self, extend_infos):
        """
        灵工支付退款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "org_hf_seq_id":self.org_hf_seq_id,
            "huifu_id":self.huifu_id,
            "ord_amt":self.ord_amt
        }
        required_params.update(extend_infos)
        return request_post(V2_FLEXIBLE_REFUND, required_params)
