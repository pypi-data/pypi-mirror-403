from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_ALIPAY_FACETOFACESIGN_APPLY



class V2MerchantDirectAlipayFacetofacesignApplyRequest(object):
    """
    支付宝直连-申请当面付代签约
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付客户Id
    huifu_id = ""
    # 上级主体ID
    upper_huifu_id = ""
    # 支付宝经营类目
    direct_category = ""
    # 开发者的应用ID
    app_id = ""
    # 联系人姓名
    contact_name = ""
    # 联系人手机号
    contact_mobile_no = ""
    # 联系人电子邮箱
    contact_email = ""
    # 商户账号
    account = ""
    # 服务费率（%）0.38~3之间，精确到0.01。当签约且授权sign_and_auth&#x3D;Y时，必填。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：0.38&lt;/font&gt;
    rate = ""
    # 文件列表
    file_list = ""

    def post(self, extend_infos):
        """
        支付宝直连-申请当面付代签约

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "upper_huifu_id":self.upper_huifu_id,
            "direct_category":self.direct_category,
            "app_id":self.app_id,
            "contact_name":self.contact_name,
            "contact_mobile_no":self.contact_mobile_no,
            "contact_email":self.contact_email,
            "account":self.account,
            "rate":self.rate,
            "file_list":self.file_list
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_ALIPAY_FACETOFACESIGN_APPLY, required_params)
