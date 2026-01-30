from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_COMPLAINT_REQUEST_CERTIFICATES



class V2MerchantComplaintRequestCertificatesRequest(object):
    """
    支付宝申诉请求凭证
    """

    # 请求汇付流水号
    req_seq_id = ""
    # 请求汇付时间
    req_date = ""
    # 支付宝推送流水号
    risk_biz_id = ""
    # 商户类型
    merchant_type = ""
    # 商户经营模式
    operation_type = ""
    # 收款应用场景
    payment_scene = ""

    def post(self, extend_infos):
        """
        支付宝申诉请求凭证

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "risk_biz_id":self.risk_biz_id,
            "merchant_type":self.merchant_type,
            "operation_type":self.operation_type,
            "payment_scene":self.payment_scene
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_COMPLAINT_REQUEST_CERTIFICATES, required_params)
