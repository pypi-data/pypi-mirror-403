from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_ALIPAY_APPAUTHTOKEN_EXCHANGE



class V2MerchantDirectAlipayAppauthtokenExchangeRequest(object):
    """
    支付宝直连-换取应用授权令牌
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付ID
    huifu_id = ""
    # 开发者的应用ID
    app_id = ""
    # 操作类型
    oper_type = ""
    # 授权码授权码，操作类型为0-换取令牌时必填，其它选填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：123&lt;/font&gt;
    app_auth_code = ""
    # 应用授权令牌应用授权令牌，操作类型为1-刷新令牌时，且该字段有值，将与数据库值进行校验；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：202208200312104378&lt;/font&gt;
    app_auth_token = ""

    def post(self, extend_infos):
        """
        支付宝直连-换取应用授权令牌

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "app_id":self.app_id,
            "oper_type":self.oper_type,
            "app_auth_code":self.app_auth_code,
            "app_auth_token":self.app_auth_token
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_ALIPAY_APPAUTHTOKEN_EXCHANGE, required_params)
