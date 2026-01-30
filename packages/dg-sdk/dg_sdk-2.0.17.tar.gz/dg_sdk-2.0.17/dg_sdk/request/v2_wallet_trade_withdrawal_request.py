from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_TRADE_WITHDRAWAL



class V2WalletTradeWithdrawalRequest(object):
    """
    钱包提现下单
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 钱包用户ID
    user_huifu_id = ""
    # 银行卡序列号
    token_no = ""
    # 提现金额
    trans_amt = ""
    # 跳转地址
    front_url = ""
    # 异步通知地址
    notify_url = ""
    # 到账日期类型
    into_acct_date_type = ""

    def post(self, extend_infos):
        """
        钱包提现下单

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "user_huifu_id":self.user_huifu_id,
            "token_no":self.token_no,
            "trans_amt":self.trans_amt,
            "front_url":self.front_url,
            "notify_url":self.notify_url,
            "into_acct_date_type":self.into_acct_date_type
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_TRADE_WITHDRAWAL, required_params)
