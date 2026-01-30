from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_TRADE_RECHARGE_CARD



class V2WalletTradeRechargeCardRequest(object):
    """
    钱包绑卡充值下单
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
    # 微信充值信息微信充值必填
    wx_rechare_info = ""
    # 支付宝充值信息支付宝充值必填
    alipay_recharge_info = ""

    def post(self, extend_infos):
        """
        钱包绑卡充值下单

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "user_huifu_id":self.user_huifu_id,
            "trans_amt":self.trans_amt,
            "wx_rechare_info":self.wx_rechare_info,
            "alipay_recharge_info":self.alipay_recharge_info
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_TRADE_RECHARGE_CARD, required_params)
