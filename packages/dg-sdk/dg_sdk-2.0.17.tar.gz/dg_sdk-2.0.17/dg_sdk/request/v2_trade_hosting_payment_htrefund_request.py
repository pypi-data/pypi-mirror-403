from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_HOSTING_PAYMENT_HTREFUND



class V2TradeHostingPaymentHtrefundRequest(object):
    """
    托管交易退款
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号
    huifu_id = ""
    # 申请退款金额
    ord_amt = ""
    # 原交易请求日期
    org_req_date = ""
    # 安全信息线上交易退款必填，参见线上退款接口；jsonObject字符串
    risk_check_data = ""
    # 设备信息线上交易退款必填，参见线上退款接口；jsonObject字符串
    terminal_device_data = ""
    # 大额转账支付账户信息数据jsonObject格式；银行大额转账支付交易退款申请时必填
    bank_info_data = ""

    def post(self, extend_infos):
        """
        托管交易退款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "ord_amt":self.ord_amt,
            "org_req_date":self.org_req_date,
            "risk_check_data":self.risk_check_data,
            "terminal_device_data":self.terminal_device_data,
            "bank_info_data":self.bank_info_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_HOSTING_PAYMENT_HTREFUND, required_params)
