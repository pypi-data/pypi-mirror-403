from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_SETTLEMENT_ENCHASHMENT_DMAMT_QUERY



class V2TradeSettlementEnchashmentDmamtQueryRequest(object):
    """
    DM取现额度查询
    """

    # 商户号
    huifu_id = ""

    def post(self, extend_infos):
        """
        DM取现额度查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_SETTLEMENT_ENCHASHMENT_DMAMT_QUERY, required_params)
