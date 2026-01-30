from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_HYC_PERSONSIGN_CREATE



class V2HycPersonsignCreateRequest(object):
    """
    个人签约发起
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 用户汇付id
    huifu_id = ""
    # 落地公司机构号
    minor_agent_id = ""
    # 乐接活请求参数jsonObject格式 合作平台为乐接活时必传
    ljh_data = ""

    def post(self, extend_infos):
        """
        个人签约发起

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "minor_agent_id":self.minor_agent_id,
            "ljh_data":self.ljh_data
        }
        required_params.update(extend_infos)
        return request_post(V2_HYC_PERSONSIGN_CREATE, required_params)
