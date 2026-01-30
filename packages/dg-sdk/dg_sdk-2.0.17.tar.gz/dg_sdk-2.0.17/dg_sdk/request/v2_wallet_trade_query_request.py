from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_TRADE_QUERY



class V2WalletTradeQueryRequest(object):
    """
    钱包交易查询
    """

    # 商户号
    huifu_id = ""
    # 原交易请求日期
    org_req_date = ""
    # 原交易请求流水号
    org_req_seq_id = ""
    # 交易类型
    trans_type = ""

    def post(self, extend_infos):
        """
        钱包交易查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "trans_type":self.trans_type
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_TRADE_QUERY, required_params)
