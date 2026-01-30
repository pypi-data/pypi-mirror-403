from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LLA_WITHHOLD_REFUND



class V2LlaWithholdRefundRequest(object):
    """
    代运营佣金代扣退款
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 原请求日期
    org_req_date = ""
    # 原请求流水号org_hf_seq_id与org_req_seq_id二选一必填。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665001&lt;/font&gt;
    org_req_seq_id = ""
    # 原全局流水号org_hf_seq_id与org_req_seq_id二选一必填。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：00470topo1A221019132207P068ac1362af00000&lt;/font&gt;
    org_hf_seq_id = ""
    # 代运营汇付id
    agency_huifu_id = ""
    # 退款金额
    trans_amt = ""
    # 设备信息
    terminal_device_data = ""
    # 安全信息
    risk_check_data = ""

    def post(self, extend_infos):
        """
        代运营佣金代扣退款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "org_hf_seq_id":self.org_hf_seq_id,
            "agency_huifu_id":self.agency_huifu_id,
            "trans_amt":self.trans_amt,
            "terminal_device_data":self.terminal_device_data,
            "risk_check_data":self.risk_check_data
        }
        required_params.update(extend_infos)
        return request_post(V2_LLA_WITHHOLD_REFUND, required_params)
