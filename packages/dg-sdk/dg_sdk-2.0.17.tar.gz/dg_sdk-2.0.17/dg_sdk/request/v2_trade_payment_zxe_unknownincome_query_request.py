from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_ZXE_UNKNOWNINCOME_QUERY



class V2TradePaymentZxeUnknownincomeQueryRequest(object):
    """
    不明来账列表查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 交易开始日期
    trans_start_date = ""
    # 交易结束日期
    trans_end_date = ""

    def post(self, extend_infos):
        """
        不明来账列表查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "trans_start_date":self.trans_start_date,
            "trans_end_date":self.trans_end_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_ZXE_UNKNOWNINCOME_QUERY, required_params)
