from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V3_BILLPAY_ORDER_PAYMENT_REFUND



class V3BillpayOrderPaymentRefundRequest(object):
    """
    账单退款接口
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 账单编号
    bill_no = ""
    # 退款金额
    ref_amt = ""
    # 大额转账支付账户信息数据jsonObject格式；银行大额转账支付交易的退款申请,付款方账户类型为对公时必填
    bank_info_data = ""

    def post(self, extend_infos):
        """
        账单退款接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bill_no":self.bill_no,
            "ref_amt":self.ref_amt,
            "bank_info_data":self.bank_info_data
        }
        required_params.update(extend_infos)
        return request_post(V3_BILLPAY_ORDER_PAYMENT_REFUND, required_params)
