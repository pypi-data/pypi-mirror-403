from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_COMPLAINT_COMPLETE



class V2MerchantComplaintCompleteRequest(object):
    """
    反馈处理完成
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 微信投诉单号
    complaint_id = ""
    # 被诉商户微信号
    complainted_mchid = ""
    # 微信商户号
    mch_id = ""

    def post(self, extend_infos):
        """
        反馈处理完成

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "complaint_id":self.complaint_id,
            "complainted_mchid":self.complainted_mchid,
            "mch_id":self.mch_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_COMPLAINT_COMPLETE, required_params)
