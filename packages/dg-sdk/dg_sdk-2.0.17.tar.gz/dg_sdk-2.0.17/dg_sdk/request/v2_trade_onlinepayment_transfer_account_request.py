from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_TRANSFER_ACCOUNT



class V2TradeOnlinepaymentTransferAccountRequest(object):
    """
    银行大额支付
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 收款方商户号
    huifu_id = ""
    # 交易金额
    trans_amt = ""
    # 商品描述
    goods_desc = ""

    def post(self, extend_infos):
        """
        银行大额支付

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "trans_amt":self.trans_amt,
            "goods_desc":self.goods_desc
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_TRANSFER_ACCOUNT, required_params)
