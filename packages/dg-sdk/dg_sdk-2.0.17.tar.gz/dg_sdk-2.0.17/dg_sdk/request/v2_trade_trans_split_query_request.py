from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_TRANS_SPLIT_QUERY



class V2TradeTransSplitQueryRequest(object):
    """
    交易分账明细查询
    """

    # 分账交易汇付全局流水号
    hf_seq_id = ""
    # 商户号
    huifu_id = ""
    # 交易类型
    ord_type = ""

    def post(self, extend_infos):
        """
        交易分账明细查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "hf_seq_id":self.hf_seq_id,
            "huifu_id":self.huifu_id,
            "ord_type":self.ord_type
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_TRANS_SPLIT_QUERY, required_params)
