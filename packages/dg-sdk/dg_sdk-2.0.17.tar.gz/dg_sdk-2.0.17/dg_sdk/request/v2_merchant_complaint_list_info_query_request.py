from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_COMPLAINT_LIST_INFO_QUERY



class V2MerchantComplaintListInfoQueryRequest(object):
    """
    查询投诉单列表及详情
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 开始日期
    begin_date = ""
    # 结束日期
    end_date = ""

    def post(self, extend_infos):
        """
        查询投诉单列表及详情

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "begin_date":self.begin_date,
            "end_date":self.end_date
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_COMPLAINT_LIST_INFO_QUERY, required_params)
