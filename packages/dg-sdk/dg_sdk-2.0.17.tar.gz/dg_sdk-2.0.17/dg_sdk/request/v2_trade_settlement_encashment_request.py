from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_SETTLEMENT_ENCASHMENT



class V2TradeSettlementEncashmentRequest(object):
    """
    取现
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 取现金额
    cash_amt = ""
    # 取现方ID号
    huifu_id = ""
    # 到账日期类型
    into_acct_date_type = ""
    # 取现卡序列号
    token_no = ""

    def post(self, extend_infos):
        """
        取现

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "cash_amt":self.cash_amt,
            "huifu_id":self.huifu_id,
            "into_acct_date_type":self.into_acct_date_type,
            "token_no":self.token_no
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_SETTLEMENT_ENCASHMENT, required_params)
