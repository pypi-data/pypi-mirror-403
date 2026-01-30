from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_FLEXIBLE_ENT



class V2FlexibleEntRequest(object):
    """
    灵工企业商户进件接口
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 渠道商号
    upper_huifu_id = ""
    # 商户角色
    mer_role = ""
    # 落地公司类型当选择落地公司时，必填;SELF-自有，COOPERATE-合作
    local_company_type = ""
    # 商户名称
    reg_name = ""
    # 商户简称
    short_name = ""
    # 证照图片
    license_pic = ""
    # 证照编号
    license_code = ""
    # 证照有效期类型
    license_validity_type = ""
    # 证照有效期开始日期
    license_begin_date = ""
    # 证照有效期截止日期格式：yyyyMMdd。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20220125&lt;/font&gt;&lt;br/&gt;  当license_validity_type&#x3D;0时必填；当license_validity_type&#x3D;1时为空；
    license_end_date = ""
    # 成立时间
    found_date = ""
    # 注册区
    reg_district_id = ""
    # 注册详细地址
    reg_detail = ""
    # 法人姓名
    legal_name = ""
    # 法人证件类型
    legal_cert_type = ""
    # 法人证件号码
    legal_cert_no = ""
    # 法人证件有效期类型
    legal_cert_validity_type = ""
    # 法人证件有效期开始日期
    legal_cert_begin_date = ""
    # 法人证件有效期截止日期日期格式：yyyyMMdd， &lt;font color&#x3D;&quot;green&quot;&gt;示例值：20220125&lt;/font&gt;&lt;br/&gt;当legal_cert_validity_type&#x3D;0时必填；&lt;br/&gt;当legal_cert_validity_type&#x3D;1时为空；&lt;br/&gt;
    legal_cert_end_date = ""
    # 法人证件地址
    legal_addr = ""
    # 法人身份证国徽面
    legal_cert_back_pic = ""
    # 法人身份证人像面
    legal_cert_front_pic = ""
    # 店铺门头照
    store_header_pic = ""
    # 联系人手机号
    contact_mobile_no = ""
    # 联系人电子邮箱
    contact_email = ""
    # 管理员账号
    login_name = ""
    # 银行卡信息配置
    card_info = ""
    # 签约人jsonObject格式；协议类型&#x3D;电子合同时，必填；
    sign_user_info = ""

    def post(self, extend_infos):
        """
        灵工企业商户进件接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "upper_huifu_id":self.upper_huifu_id,
            "mer_role":self.mer_role,
            "local_company_type":self.local_company_type,
            "reg_name":self.reg_name,
            "short_name":self.short_name,
            "license_pic":self.license_pic,
            "license_code":self.license_code,
            "license_validity_type":self.license_validity_type,
            "license_begin_date":self.license_begin_date,
            "license_end_date":self.license_end_date,
            "found_date":self.found_date,
            "reg_district_id":self.reg_district_id,
            "reg_detail":self.reg_detail,
            "legal_name":self.legal_name,
            "legal_cert_type":self.legal_cert_type,
            "legal_cert_no":self.legal_cert_no,
            "legal_cert_validity_type":self.legal_cert_validity_type,
            "legal_cert_begin_date":self.legal_cert_begin_date,
            "legal_cert_end_date":self.legal_cert_end_date,
            "legal_addr":self.legal_addr,
            "legal_cert_back_pic":self.legal_cert_back_pic,
            "legal_cert_front_pic":self.legal_cert_front_pic,
            "store_header_pic":self.store_header_pic,
            "contact_mobile_no":self.contact_mobile_no,
            "contact_email":self.contact_email,
            "login_name":self.login_name,
            "card_info":self.card_info,
            "sign_user_info":self.sign_user_info
        }
        required_params.update(extend_infos)
        return request_post(V2_FLEXIBLE_ENT, required_params)
