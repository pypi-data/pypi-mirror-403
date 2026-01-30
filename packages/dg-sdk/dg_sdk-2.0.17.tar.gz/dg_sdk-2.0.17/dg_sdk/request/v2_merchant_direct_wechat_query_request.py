from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_WECHAT_QUERY



class V2MerchantDirectWechatQueryRequest(object):
    """
    查询微信申请状态
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 开发者的应用ID
    app_id = ""
    # 微信商户号
    mch_id = ""

    def post(self, extend_infos):
        """
        查询微信申请状态

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "app_id":self.app_id,
            "mch_id":self.mch_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_WECHAT_QUERY, required_params)
