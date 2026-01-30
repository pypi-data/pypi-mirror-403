from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_WXUSERMARK_QUERY



class V2TradeWxusermarkQueryRequest(object):
    """
    微信用户标识查询接口
    """

    # 商户号
    huifu_id = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 支付授权码
    auth_code = ""

    def post(self, extend_infos):
        """
        微信用户标识查询接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "auth_code":self.auth_code
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_WXUSERMARK_QUERY, required_params)
