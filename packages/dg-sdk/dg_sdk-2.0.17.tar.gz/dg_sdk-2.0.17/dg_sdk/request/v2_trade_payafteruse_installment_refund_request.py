from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYAFTERUSE_INSTALLMENT_REFUND



class V2TradePayafteruseInstallmentRefundRequest(object):
    """
    分期交易退款
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号
    huifu_id = ""
    # 申请退款金额
    ord_amt = ""
    # 原请求日期
    org_req_date = ""

    def post(self, extend_infos):
        """
        分期交易退款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "ord_amt":self.ord_amt,
            "org_req_date":self.org_req_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYAFTERUSE_INSTALLMENT_REFUND, required_params)
