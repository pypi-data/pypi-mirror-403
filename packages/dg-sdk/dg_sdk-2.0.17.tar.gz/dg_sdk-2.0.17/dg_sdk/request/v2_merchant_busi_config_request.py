from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_CONFIG



class V2MerchantBusiConfigRequest(object):
    """
    微信商户配置
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付客户Id
    huifu_id = ""
    # 业务开通类型
    fee_type = ""
    # 公众号支付Appid条件必填，&lt;font color&#x3D;&quot;green&quot;&gt;示例值：wx3767c5bd01df5061&lt;/font&gt; ；wx_woa_app_id 、wx_woa_path、micro_sub_appid和 wx_applet_app_id四者不能同时为空
    wx_woa_app_id = ""
    # 微信公众号授权目录条件必填，&lt;font color&#x3D;&quot;green&quot;&gt;示例值：https://paas.huifu.com/shouyintai/demo/h5/&lt;/font&gt;；wx_woa_app_id 、wx_woa_path、micro_sub_appid和 wx_applet_app_id四者不能同时为空
    wx_woa_path = ""
    # 微信小程序APPID条件必填，&lt;font color&#x3D;&quot;green&quot;&gt;示例值：wx8523175fea790f10&lt;/font&gt; ；wx_woa_app_id 、wx_woa_path、micro_sub_appid和 wx_applet_app_id四者不能同时为空
    wx_applet_app_id = ""

    def post(self, extend_infos):
        """
        微信商户配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "fee_type":self.fee_type,
            "wx_woa_app_id":self.wx_woa_app_id,
            "wx_woa_path":self.wx_woa_path,
            "wx_applet_app_id":self.wx_applet_app_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_CONFIG, required_params)
