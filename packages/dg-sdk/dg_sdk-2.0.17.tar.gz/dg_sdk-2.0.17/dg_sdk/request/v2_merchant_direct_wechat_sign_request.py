from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_WECHAT_SIGN



class V2MerchantDirectWechatSignRequest(object):
    """
    微信特约商户进件
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 渠道商汇付Id
    upper_huifu_id = ""
    # 开发者的应用ID
    app_id = ""
    # 商户号
    mch_id = ""
    # 经营者/法人是否为受益人
    owner = ""
    # 超级管理员信息
    contact_info = ""
    # 经营场景类型
    sales_scenes_type = ""
    # 经营场景
    sales_info = ""
    # 结算信息
    settlement_info = ""

    def post(self, extend_infos):
        """
        微信特约商户进件

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "upper_huifu_id":self.upper_huifu_id,
            "app_id":self.app_id,
            "mch_id":self.mch_id,
            "owner":self.owner,
            "contact_info":self.contact_info,
            "sales_scenes_type":self.sales_scenes_type,
            "sales_info":self.sales_info,
            "settlement_info":self.settlement_info
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_WECHAT_SIGN, required_params)
