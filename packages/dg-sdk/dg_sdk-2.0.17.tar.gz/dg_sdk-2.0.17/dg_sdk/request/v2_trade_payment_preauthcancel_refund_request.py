from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_PREAUTHCANCEL_REFUND



class V2TradePaymentPreauthcancelRefundRequest(object):
    """
    微信支付宝预授权撤销
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 客户号
    huifu_id = ""
    # 原交易请求日期
    org_req_date = ""
    # 撤销金额
    ord_amt = ""
    # 风控信息
    risk_check_info = ""

    def post(self, extend_infos):
        """
        微信支付宝预授权撤销

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "ord_amt":self.ord_amt,
            "risk_check_info":self.risk_check_info
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_PREAUTHCANCEL_REFUND, required_params)
