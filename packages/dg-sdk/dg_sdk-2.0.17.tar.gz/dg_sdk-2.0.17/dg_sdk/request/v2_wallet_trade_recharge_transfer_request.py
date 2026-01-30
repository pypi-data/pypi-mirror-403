from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_TRADE_RECHARGE_TRANSFER



class V2WalletTradeRechargeTransferRequest(object):
    """
    用户补贴
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 出款方商户号
    huifu_id = ""
    # 收款方用户号
    user_huifu_id = ""
    # 转账金额
    trans_amt = ""

    def post(self, extend_infos):
        """
        用户补贴

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "user_huifu_id":self.user_huifu_id,
            "trans_amt":self.trans_amt
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_TRADE_RECHARGE_TRANSFER, required_params)
