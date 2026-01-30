from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_SETTLE_COLLECTION_RULE_MODIFY



class V2TradeSettleCollectionRuleModifyRequest(object):
    """
    修改归集配置
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 转出方商户号
    out_huifu_id = ""
    # 转出方账户号
    out_acct_id = ""

    def post(self, extend_infos):
        """
        修改归集配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "out_huifu_id":self.out_huifu_id,
            "out_acct_id":self.out_acct_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_SETTLE_COLLECTION_RULE_MODIFY, required_params)
