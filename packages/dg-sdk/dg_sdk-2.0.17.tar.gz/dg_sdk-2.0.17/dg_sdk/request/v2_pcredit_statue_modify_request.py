from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_PCREDIT_STATUE_MODIFY



class V2PcreditStatueModifyRequest(object):
    """
    上架下架分期活动接口
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 贴息方案实例id
    solution_id = ""
    # 状态控制
    status = ""

    def post(self, extend_infos):
        """
        上架下架分期活动接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "solution_id":self.solution_id,
            "status":self.status
        }
        required_params.update(extend_infos)
        return request_post(V2_PCREDIT_STATUE_MODIFY, required_params)
