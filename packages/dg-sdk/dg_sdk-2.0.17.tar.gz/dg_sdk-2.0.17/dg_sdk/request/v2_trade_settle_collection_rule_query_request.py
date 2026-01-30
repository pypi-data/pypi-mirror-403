from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_SETTLE_COLLECTION_RULE_QUERY



class V2TradeSettleCollectionRuleQueryRequest(object):
    """
    归集配置查询
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 转出方商户号转出方商户号和转入方商户号二选一必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：6666000123123124&lt;/font&gt;
    out_huifu_id = ""
    # 转入方商户号转出方商户号和转入方商户号二选一必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：6666000123123124&lt;/font&gt;
    in_huifu_id = ""

    def post(self, extend_infos):
        """
        归集配置查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "out_huifu_id":self.out_huifu_id,
            "in_huifu_id":self.in_huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_SETTLE_COLLECTION_RULE_QUERY, required_params)
