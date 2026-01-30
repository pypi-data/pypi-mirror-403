from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_COMPLAINT_QUERY_STATUS



class V2MerchantComplaintQueryStatusRequest(object):
    """
    支付宝申诉查询
    """

    # 请求汇付流水号
    req_seq_id = ""
    # 请求汇付时间
    req_date = ""
    # 支付宝推送流水号
    risk_biz_id = ""
    # 申诉的商户
    bank_mer_code = ""

    def post(self, extend_infos):
        """
        支付宝申诉查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "risk_biz_id":self.risk_biz_id,
            "bank_mer_code":self.bank_mer_code
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_COMPLAINT_QUERY_STATUS, required_params)
