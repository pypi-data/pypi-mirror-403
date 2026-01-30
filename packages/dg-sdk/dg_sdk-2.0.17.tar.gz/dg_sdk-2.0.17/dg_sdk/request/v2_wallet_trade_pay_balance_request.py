from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_TRADE_PAY_BALANCE



class V2WalletTradePayBalanceRequest(object):
    """
    钱包支付下单
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 钱包用户ID
    user_huifu_id = ""
    # 订单金额
    trans_amt = ""
    # 跳转地址
    front_url = ""

    def post(self, extend_infos):
        """
        钱包支付下单

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "user_huifu_id":self.user_huifu_id,
            "trans_amt":self.trans_amt,
            "front_url":self.front_url
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_TRADE_PAY_BALANCE, required_params)
