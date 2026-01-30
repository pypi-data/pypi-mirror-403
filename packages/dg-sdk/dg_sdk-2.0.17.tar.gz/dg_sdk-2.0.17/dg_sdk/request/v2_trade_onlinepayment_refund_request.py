from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_REFUND



class V2TradeOnlinepaymentRefundRequest(object):
    """
    线上交易退款
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号
    huifu_id = ""
    # 退款金额
    ord_amt = ""
    # 设备信息条件必填，当为银行大额支付时可不填，jsonObject格式
    terminal_device_data = ""
    # 安全信息条件必填，当为银行大额支付时可不填，jsonObject格式
    risk_check_data = ""

    def post(self, extend_infos):
        """
        线上交易退款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "ord_amt":self.ord_amt,
            "terminal_device_data":self.terminal_device_data,
            "risk_check_data":self.risk_check_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_REFUND, required_params)
