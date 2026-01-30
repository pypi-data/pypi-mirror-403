from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_ZXE_ACCTDETAIL_QUERY



class V2TradePaymentZxeAcctdetailQueryRequest(object):
    """
    E账户账务明细查询
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号/用户号
    huifu_id = ""
    # 交易日期
    trans_date = ""
    # 交易类型
    trans_type = ""

    def post(self, extend_infos):
        """
        E账户账务明细查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "trans_date":self.trans_date,
            "trans_type":self.trans_type
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_ZXE_ACCTDETAIL_QUERY, required_params)
