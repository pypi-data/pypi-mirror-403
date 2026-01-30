from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_BILL_ENT_REFUND_QUERY



class V2BillEntRefundQueryRequest(object):
    """
    企业账单退款查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 退款请求时间
    org_req_date = ""
    # 退款请求流水号
    org_req_seq_id = ""

    def post(self, extend_infos):
        """
        企业账单退款查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_BILL_ENT_REFUND_QUERY, required_params)
