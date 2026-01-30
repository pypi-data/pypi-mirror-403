from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_PCREDIT_ORDER_QUERY



class V2PcreditOrderQueryRequest(object):
    """
    花呗分期贴息查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付客户Id
    huifu_id = ""
    # 贴息方案id
    solution_id = ""
    # 活动开始时间
    start_time = ""
    # 活动结束时间
    end_time = ""

    def post(self, extend_infos):
        """
        花呗分期贴息查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "solution_id":self.solution_id,
            "start_time":self.start_time,
            "end_time":self.end_time
        }
        required_params.update(extend_infos)
        return request_post(V2_PCREDIT_ORDER_QUERY, required_params)
