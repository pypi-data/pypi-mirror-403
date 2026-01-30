from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_QUICKPAY_FRONTPAY



class V2TradeOnlinepaymentQuickpayFrontpayRequest(object):
    """
    快捷支付页面版
    """

    # 业务请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 订单金额
    trans_amt = ""
    # 银行扩展信息
    extend_pay_data = ""
    # 设备信息
    terminal_device_data = ""
    # 安全信息
    risk_check_data = ""
    # 异步通知地址
    notify_url = ""

    def post(self, extend_infos):
        """
        快捷支付页面版

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "trans_amt":self.trans_amt,
            "extend_pay_data":self.extend_pay_data,
            "terminal_device_data":self.terminal_device_data,
            "risk_check_data":self.risk_check_data,
            "notify_url":self.notify_url
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_QUICKPAY_FRONTPAY, required_params)
