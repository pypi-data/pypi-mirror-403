from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V3_TRADE_ONLINEPAYMENT_QUICKPAY_PAY



class V3TradeOnlinepaymentQuickpayPayRequest(object):
    """
    快捷支付
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 短信验证码
    sms_code = ""

    def post(self, extend_infos):
        """
        快捷支付

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "sms_code":self.sms_code
        }
        required_params.update(extend_infos)
        return request_post(V3_TRADE_ONLINEPAYMENT_QUICKPAY_PAY, required_params)
