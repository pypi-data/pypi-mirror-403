from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_USERMARK2_QUERY



class V2TradePaymentUsermark2QueryRequest(object):
    """
    获取银联用户标识接口
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号
    huifu_id = ""
    # 授权码
    auth_code = ""
    # 银联支付标识
    app_up_identifier = ""

    def post(self, extend_infos):
        """
        获取银联用户标识接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "auth_code":self.auth_code,
            "app_up_identifier":self.app_up_identifier
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_USERMARK2_QUERY, required_params)
