from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_APPEAL_RELATEDCLUE_QUERY



class V2MerchantAppealRelatedclueQueryRequest(object):
    """
    关联线索查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 分页条数
    page_size = ""
    # 协查单号
    assist_id = ""

    def post(self, extend_infos):
        """
        关联线索查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "page_size":self.page_size,
            "assist_id":self.assist_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_APPEAL_RELATEDCLUE_QUERY, required_params)
