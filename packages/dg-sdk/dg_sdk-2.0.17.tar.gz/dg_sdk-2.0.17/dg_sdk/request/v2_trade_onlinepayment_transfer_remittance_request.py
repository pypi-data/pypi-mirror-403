from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_TRANSFER_REMITTANCE



class V2TradeOnlinepaymentTransferRemittanceRequest(object):
    """
    汇付入账通知
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 交易金额
    trans_amt = ""
    # 异步通知地址
    notify_url = ""
    # 原汇付通道流水号
    org_remittance_order_id = ""
    # 商品描述
    goods_desc = ""

    def post(self, extend_infos):
        """
        汇付入账通知

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "trans_amt":self.trans_amt,
            "notify_url":self.notify_url,
            "org_remittance_order_id":self.org_remittance_order_id,
            "goods_desc":self.goods_desc
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_TRANSFER_REMITTANCE, required_params)
