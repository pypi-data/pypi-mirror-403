from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_CARDBIN_QUERY



class V2TradeCardbinQueryRequest(object):
    """
    卡bin信息查询
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 银行卡号密文
    bank_card_no_crypt = ""

    def post(self, extend_infos):
        """
        卡bin信息查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "bank_card_no_crypt":self.bank_card_no_crypt
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_CARDBIN_QUERY, required_params)
