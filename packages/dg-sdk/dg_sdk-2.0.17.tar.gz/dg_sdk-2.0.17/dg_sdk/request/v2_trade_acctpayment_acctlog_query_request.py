from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ACCTPAYMENT_ACCTLOG_QUERY



class V2TradeAcctpaymentAcctlogQueryRequest(object):
    """
    账务流水查询
    """

    # 请求流水号
    req_seq_id = ""
    # 渠道/代理/商户/用户编号
    huifu_id = ""
    # 账务日期
    acct_date = ""

    def post(self, extend_infos):
        """
        账务流水查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "acct_date":self.acct_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ACCTPAYMENT_ACCTLOG_QUERY, required_params)
