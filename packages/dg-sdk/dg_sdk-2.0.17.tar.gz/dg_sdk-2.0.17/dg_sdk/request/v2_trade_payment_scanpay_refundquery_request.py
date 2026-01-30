from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_SCANPAY_REFUNDQUERY



class V2TradePaymentScanpayRefundqueryRequest(object):
    """
    扫码交易退款查询
    """

    # 商户号
    huifu_id = ""
    # 退款请求日期退款发生的日期，格式为yyyyMMdd，&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20220925&lt;/font&gt;；&lt;/br&gt;传入退款全局流水号时，非必填，其他场景必填；
    org_req_date = ""
    # 退款全局流水号退款请求流水号,退款全局流水号,终端订单号三选一不能都为空；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：0030default220825182711P099ac1f343f00000&lt;/font&gt;
    org_hf_seq_id = ""
    # 退款请求流水号退款请求流水号,退款全局流水号,终端订单号三选一不能都为空；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：202110210012100005&lt;/font&gt;
    org_req_seq_id = ""
    # 终端订单号退款请求流水号,退款全局流水号,终端订单号三选一不能都为空；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：16672670833524393&lt;/font&gt;
    mer_ord_id = ""

    def post(self, extend_infos):
        """
        扫码交易退款查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_hf_seq_id":self.org_hf_seq_id,
            "org_req_seq_id":self.org_req_seq_id,
            "mer_ord_id":self.mer_ord_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_SCANPAY_REFUNDQUERY, required_params)
