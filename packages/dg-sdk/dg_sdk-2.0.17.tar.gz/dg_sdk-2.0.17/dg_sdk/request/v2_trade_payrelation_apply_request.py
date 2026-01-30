from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYRELATION_APPLY



class V2TradePayrelationApplyRequest(object):
    """
    付款关系提交
    """

    # 出款方商户号
    out_huifu_id = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 付款关系明细
    pay_relations = ""

    def post(self, extend_infos):
        """
        付款关系提交

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "out_huifu_id":self.out_huifu_id,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "pay_relations":self.pay_relations
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYRELATION_APPLY, required_params)
