from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_TRANSFER_BANKMISTAKE_APPLYQUERY



class V2TradeOnlinepaymentTransferBankmistakeApplyqueryRequest(object):
    """
    银行大额支付差错申请查询
    """

    # 商户号
    huifu_id = ""
    # 原请求日期
    org_req_date = ""
    # 原请求流水号
    org_req_seq_id = ""
    # 订单类型
    order_type = ""

    def post(self, extend_infos):
        """
        银行大额支付差错申请查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "order_type":self.order_type
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_TRANSFER_BANKMISTAKE_APPLYQUERY, required_params)
