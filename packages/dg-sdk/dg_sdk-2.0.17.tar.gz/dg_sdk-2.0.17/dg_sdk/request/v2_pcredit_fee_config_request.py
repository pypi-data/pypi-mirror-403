from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_PCREDIT_FEE_CONFIG



class V2PcreditFeeConfigRequest(object):
    """
    商户分期配置
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""

    def post(self, extend_infos):
        """
        商户分期配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_PCREDIT_FEE_CONFIG, required_params)
