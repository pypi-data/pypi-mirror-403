from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_APPEAL_LOG_QUERY



class V2MerchantAppealLogQueryRequest(object):
    """
    操作日志查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 分页条数
    page_size = ""
    # 申诉单号
    appeal_id = ""

    def post(self, extend_infos):
        """
        操作日志查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "page_size":self.page_size,
            "appeal_id":self.appeal_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_APPEAL_LOG_QUERY, required_params)
