from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_SETTLEMENT_QUERY



class V2TradeSettlementQueryRequest(object):
    """
    出金交易查询
    """

    # 汇付客户Id
    huifu_id = ""
    # 原交易请求日期
    org_req_date = ""
    # 原交易返回的全局流水号原交易返回的全局流水号、原交易请求流水号二选一必填；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：00470topo1A211015160805P090ac132fef00000&lt;/font&gt;
    org_hf_seq_id = ""
    # 原交易请求流水号原交易返回的全局流水号、原交易请求流水号二选一必填；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：202109167745558220003&lt;/font&gt;
    org_req_seq_id = ""

    def post(self, extend_infos):
        """
        出金交易查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_hf_seq_id":self.org_hf_seq_id,
            "org_req_seq_id":self.org_req_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_SETTLEMENT_QUERY, required_params)
