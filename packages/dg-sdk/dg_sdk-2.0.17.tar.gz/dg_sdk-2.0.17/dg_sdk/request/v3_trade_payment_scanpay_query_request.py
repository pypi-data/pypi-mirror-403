from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V3_TRADE_PAYMENT_SCANPAY_QUERY



class V3TradePaymentScanpayQueryRequest(object):
    """
    扫码交易查询
    """

    # 汇付商户号
    huifu_id = ""
    # 原机构请求日期格式为yyyyMMdd，&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20220125&lt;/font&gt;；&lt;/br&gt;传入org_hf_seq_id时非必填，其他场景必填；
    org_req_date = ""
    # 汇付服务订单号out_ord_id,org_hf_seq_id,org_req_seq_id 必填其一；汇付生成的服务订单号；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：1234323JKHDFE1243252&lt;/font&gt;
    out_ord_id = ""
    # 创建服务订单返回的汇付全局流水号out_ord_id,org_hf_seq_id,org_req_seq_id 必填其一；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：00290TOP1GR210919004230P853ac13262200000&lt;/font&gt;
    org_hf_seq_id = ""
    # 服务订单创建请求流水号out_ord_id,org_hf_seq_id,org_req_seq_id 必填其一；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：202110210012100005&lt;/font&gt;
    org_req_seq_id = ""

    def post(self, extend_infos):
        """
        扫码交易查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "out_ord_id":self.out_ord_id,
            "org_hf_seq_id":self.org_hf_seq_id,
            "org_req_seq_id":self.org_req_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V3_TRADE_PAYMENT_SCANPAY_QUERY, required_params)
