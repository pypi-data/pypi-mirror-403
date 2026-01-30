from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_QUICKPAY_SMSCHECK



class V2TradeOnlinepaymentQuickpaySmscheckRequest(object):
    """
    快捷支付短信预校验
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 原请求日期
    org_req_date = ""
    # 原请求流水号
    org_req_seq_id = ""
    # 短信验证码
    sms_code = ""

    def post(self, extend_infos):
        """
        快捷支付短信预校验

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "sms_code":self.sms_code
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_QUICKPAY_SMSCHECK, required_params)
