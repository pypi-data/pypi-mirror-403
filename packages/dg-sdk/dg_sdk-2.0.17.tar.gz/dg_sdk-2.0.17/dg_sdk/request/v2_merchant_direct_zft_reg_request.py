from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_ZFT_REG



class V2MerchantDirectZftRegRequest(object):
    """
    直付通商户入驻
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付ID
    huifu_id = ""
    # 进件的二级商户名称
    name = ""
    # 商家类型
    merchant_type = ""
    # 商户经营类目
    mcc = ""
    # 商户证件类型
    cert_type = ""
    # 商户证件编号
    cert_no = ""
    # 证件名称目前只有个体工商户商户类型要求填入本字段，填写值为个体工商户营业执照上的名称。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：xxxx小卖铺&lt;/font&gt;
    cert_name = ""
    # 法人名称仅个人商户非必填，其他必填。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：张三&lt;/font&gt;
    legal_name = ""
    # 法人证件号码仅个人商户非必填，其他必填。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：3209261975120284333&lt;/font&gt;
    legal_cert_no = ""
    # 客服电话
    service_phone = ""
    # 经营省
    prov_id = ""
    # 经营市
    area_id = ""
    # 经营区
    district_id = ""
    # 经营详细地址
    detail_addr = ""
    # 联系人姓名
    contact_name = ""
    # 商户联系人业务标识
    contact_tag = ""
    # 联系人类型
    contact_type = ""
    # 联系人手机号
    contact_mobile_no = ""
    # 商户结算卡信息jsonArray格式。本业务当前只允许传入一张结算卡。与支付宝账号字段二选一必填
    zft_card_info_list = ""
    # 商户支付宝账号商户支付宝账号，用作结算账号。与银行卡对象字段二选一必填。&lt;br/&gt;本字段要求支付宝账号的名称与商户名称mch_name同名，且是实名认证过的支付宝账户。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：test@huifu.com&lt;/font&gt;
    alipay_logon_id = ""
    # 商户行业资质类型当商户是特殊行业时必填，具体取值[参见表格](https://mif-pub.alipayobjects.com/QualificationType.xlsx)。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：310&lt;/font&gt;
    industry_qualification_type = ""
    # 商户使用服务
    service = ""
    # 商户与服务商的签约时间
    sign_time_with_isv = ""
    # 商户支付宝账户用于协议确认。目前商业场景（除医疗、中小学教育等）下必填。本字段要求上送的支付宝账号的名称与商户名称name同名，且是实名认证支付宝账户。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：test@huifu.com&lt;/font&gt;
    binding_alipay_logon_id = ""
    # 默认结算类型
    default_settle_type = ""
    # 文件列表
    file_list = ""

    def post(self, extend_infos):
        """
        直付通商户入驻

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "name":self.name,
            "merchant_type":self.merchant_type,
            "mcc":self.mcc,
            "cert_type":self.cert_type,
            "cert_no":self.cert_no,
            "cert_name":self.cert_name,
            "legal_name":self.legal_name,
            "legal_cert_no":self.legal_cert_no,
            "service_phone":self.service_phone,
            "prov_id":self.prov_id,
            "area_id":self.area_id,
            "district_id":self.district_id,
            "detail_addr":self.detail_addr,
            "contact_name":self.contact_name,
            "contact_tag":self.contact_tag,
            "contact_type":self.contact_type,
            "contact_mobile_no":self.contact_mobile_no,
            "zft_card_info_list":self.zft_card_info_list,
            "alipay_logon_id":self.alipay_logon_id,
            "industry_qualification_type":self.industry_qualification_type,
            "service":self.service,
            "sign_time_with_isv":self.sign_time_with_isv,
            "binding_alipay_logon_id":self.binding_alipay_logon_id,
            "default_settle_type":self.default_settle_type,
            "file_list":self.file_list
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_ZFT_REG, required_params)
