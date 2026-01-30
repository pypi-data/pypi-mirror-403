from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_COMPLAINT_SUBMIT_CERTIFICATES



class V2MerchantComplaintSubmitCertificatesRequest(object):
    """
    支付宝申诉提交凭证
    """

    # 请求汇付流水号
    req_seq_id = ""
    # 请求汇付时间
    req_date = ""
    # 支付宝推送流水号
    risk_biz_id = ""
    # 申诉解限的唯一ID
    relieving_id = ""
    # 解限风险类型
    relieve_risk_type = ""
    # 提交的凭证数据
    relieve_cert_data_list = ""

    def post(self, extend_infos):
        """
        支付宝申诉提交凭证

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "risk_biz_id":self.risk_biz_id,
            "relieving_id":self.relieving_id,
            "relieve_risk_type":self.relieve_risk_type,
            "relieve_cert_data_list":self.relieve_cert_data_list
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_COMPLAINT_SUBMIT_CERTIFICATES, required_params)
