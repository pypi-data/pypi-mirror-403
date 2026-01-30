from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_SETTLEMENT_CLEARING_QUERY



class V2TradeSettlementClearingQueryRequest(object):
    """
    电子账户资金清分结果查询
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 清分文件ID
    file_id = ""

    def post(self, extend_infos):
        """
        电子账户资金清分结果查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "file_id":self.file_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_SETTLEMENT_CLEARING_QUERY, required_params)
