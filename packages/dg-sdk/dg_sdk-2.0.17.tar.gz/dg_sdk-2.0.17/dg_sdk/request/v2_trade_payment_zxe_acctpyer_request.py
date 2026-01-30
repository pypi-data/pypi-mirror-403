from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_ZXE_ACCTPYER



class V2TradePaymentZxeAcctpyerRequest(object):
    """
    电子账户付款
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 出款方商户号
    out_huifu_id = ""
    # 订单金额
    trans_amt = ""
    # 三方支付数据
    third_pay_data = ""

    def post(self, extend_infos):
        """
        电子账户付款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "out_huifu_id":self.out_huifu_id,
            "trans_amt":self.trans_amt,
            "third_pay_data":self.third_pay_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_ZXE_ACCTPYER, required_params)
