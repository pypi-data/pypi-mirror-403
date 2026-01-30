from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_TRADE_PAY_REFUND_QUERY



class V2WalletTradePayRefundQueryRequest(object):
    """
    钱包支付退款查询
    """

    # 原退款交易请求日期
    org_req_date = ""
    # 原退款交易请求流水号
    org_req_seq_id = ""

    def post(self, extend_infos):
        """
        钱包支付退款查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_TRADE_PAY_REFUND_QUERY, required_params)
