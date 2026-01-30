from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_COMPLAINT_REPLY



class V2MerchantComplaintReplyRequest(object):
    """
    回复用户
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 微信投诉单号
    complaint_id = ""
    # 被诉商户微信号
    complainted_mchid = ""
    # 回复内容
    response_content = ""
    # 微信商户号
    mch_id = ""

    def post(self, extend_infos):
        """
        回复用户

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "complaint_id":self.complaint_id,
            "complainted_mchid":self.complainted_mchid,
            "response_content":self.response_content,
            "mch_id":self.mch_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_COMPLAINT_REPLY, required_params)
