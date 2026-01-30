from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_WECHAT_SUBSCRIBE_QUERY



class V2MerchantDirectWechatSubscribeQueryRequest(object):
    """
    微信直连-微信关注配置查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付ID
    huifu_id = ""
    # 开发者的应用ID
    app_id = ""
    # 商户号
    mch_id = ""
    # 特约商户号
    sub_mchid = ""

    def post(self, extend_infos):
        """
        微信直连-微信关注配置查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "app_id":self.app_id,
            "mch_id":self.mch_id,
            "sub_mchid":self.sub_mchid
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_WECHAT_SUBSCRIBE_QUERY, required_params)
