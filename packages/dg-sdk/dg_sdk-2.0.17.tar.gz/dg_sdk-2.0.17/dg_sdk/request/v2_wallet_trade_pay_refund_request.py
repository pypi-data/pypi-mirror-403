from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_TRADE_PAY_REFUND



class V2WalletTradePayRefundRequest(object):
    """
    钱包支付退款
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 钱包用户ID
    user_huifu_id = ""
    # 退款金额
    trans_amt = ""
    # 原交易请求日期
    org_req_date = ""

    def post(self, extend_infos):
        """
        钱包支付退款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "user_huifu_id":self.user_huifu_id,
            "trans_amt":self.trans_amt,
            "org_req_date":self.org_req_date
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_TRADE_PAY_REFUND, required_params)
