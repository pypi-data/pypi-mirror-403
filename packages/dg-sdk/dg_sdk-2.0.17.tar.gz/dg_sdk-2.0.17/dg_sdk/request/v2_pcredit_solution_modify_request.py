from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_PCREDIT_SOLUTION_MODIFY



class V2PcreditSolutionModifyRequest(object):
    """
    更新花呗分期方案
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付客户Id
    huifu_id = ""
    # 创建成功后返回的贴息活动方案id
    solution_id = ""

    def post(self, extend_infos):
        """
        更新花呗分期方案

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "solution_id":self.solution_id
        }
        required_params.update(extend_infos)
        return request_post(V2_PCREDIT_SOLUTION_MODIFY, required_params)
