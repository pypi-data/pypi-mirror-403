from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_TRANSFER_ACCOUNT_CLOSE



class V2TradeOnlinepaymentTransferAccountCloseRequest(object):
    """
    银行大额支付关单
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 原请求流水号
    org_req_seq_id = ""
    # 原请求日期
    org_req_date = ""

    def post(self, extend_infos):
        """
        银行大额支付关单

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "org_req_seq_id":self.org_req_seq_id,
            "org_req_date":self.org_req_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_TRANSFER_ACCOUNT_CLOSE, required_params)
