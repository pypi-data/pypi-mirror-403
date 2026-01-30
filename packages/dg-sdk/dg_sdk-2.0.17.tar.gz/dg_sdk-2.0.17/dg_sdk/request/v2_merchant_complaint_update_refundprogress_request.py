from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_COMPLAINT_UPDATE_REFUNDPROGRESS



class V2MerchantComplaintUpdateRefundprogressRequest(object):
    """
    更新退款审批结果
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 投诉单号
    complaint_id = ""
    # 审批动作
    action = ""
    # 微信商户号
    mch_id = ""

    def post(self, extend_infos):
        """
        更新退款审批结果

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "complaint_id":self.complaint_id,
            "action":self.action,
            "mch_id":self.mch_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_COMPLAINT_UPDATE_REFUNDPROGRESS, required_params)
