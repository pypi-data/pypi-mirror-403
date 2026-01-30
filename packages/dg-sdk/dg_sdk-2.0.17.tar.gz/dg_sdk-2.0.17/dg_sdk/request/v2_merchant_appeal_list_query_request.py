from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_APPEAL_LIST_QUERY



class V2MerchantAppealListQueryRequest(object):
    """
    申诉单列表查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 分页条数
    page_size = ""
    # 申诉创建开始日期
    begin_date = ""
    # 申诉创建结束日期
    end_date = ""

    def post(self, extend_infos):
        """
        申诉单列表查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "page_size":self.page_size,
            "begin_date":self.begin_date,
            "end_date":self.end_date
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_APPEAL_LIST_QUERY, required_params)
