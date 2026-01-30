from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LLA_WITHHOLD_REFUND_QUERY



class V2LlaWithholdRefundQueryRequest(object):
    """
    代运营佣金代扣退款查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 原退款请求日期
    org_req_date = ""
    # 原退款请求流水号org_hf_seq_id与org_req_seq_id二选一必填。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665001&lt;/font&gt;
    org_req_seq_id = ""
    # 原退款全局流水号org_hf_seq_id与org_req_seq_id二选一必填。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：00470topo1A221019132207P068ac1362af00000&lt;/font&gt;
    org_hf_seq_id = ""
    # 代运营汇付id
    agency_huifu_id = ""

    def post(self, extend_infos):
        """
        代运营佣金代扣退款查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "org_hf_seq_id":self.org_hf_seq_id,
            "agency_huifu_id":self.agency_huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_LLA_WITHHOLD_REFUND_QUERY, required_params)
