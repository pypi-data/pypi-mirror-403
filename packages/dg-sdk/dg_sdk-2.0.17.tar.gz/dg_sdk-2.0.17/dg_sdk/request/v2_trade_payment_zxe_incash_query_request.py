from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_ZXE_INCASH_QUERY



class V2TradePaymentZxeIncashQueryRequest(object):
    """
    E账户转账及充值查询接口
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号/用户号
    huifu_id = ""

    def post(self, extend_infos):
        """
        E账户转账及充值查询接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_ZXE_INCASH_QUERY, required_params)
