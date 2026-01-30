from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYSCORE_DEDUCT_QUERY



class V2TradePayscoreDeductQueryRequest(object):
    """
    查询扣款信息
    """

    # 汇付商户号
    huifu_id = ""

    def post(self, extend_infos):
        """
        查询扣款信息

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYSCORE_DEDUCT_QUERY, required_params)
