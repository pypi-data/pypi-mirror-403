from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_PCREDIT_SOLUTION_QUERY



class V2PcreditSolutionQueryRequest(object):
    """
    花呗分期活动查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付Id
    huifu_id = ""
    # 活动方案id
    solution_id = ""

    def post(self, extend_infos):
        """
        花呗分期活动查询

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
        return request_post(V2_PCREDIT_SOLUTION_QUERY, required_params)
