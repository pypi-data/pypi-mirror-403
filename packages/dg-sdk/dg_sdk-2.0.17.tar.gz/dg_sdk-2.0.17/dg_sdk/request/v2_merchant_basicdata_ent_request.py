from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BASICDATA_ENT



class V2MerchantBasicdataEntRequest(object):
    """
    企业商户进件
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 渠道商号
    upper_huifu_id = ""
    # 商户名称
    reg_name = ""
    # 商户简称
    short_name = ""
    # 小票名称
    receipt_name = ""
    # 公司类型
    ent_type = ""
    # 所属行业参考[汇付MCC编码](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_hfmccbm) ；当use_head_info_flag&#x3D;Y时不填&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：5311&lt;/font&gt;
    mcc = ""
    # 经营类型1：实体，2：虚拟 ；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：1&lt;/font&gt; ；当use_head_info_flag&#x3D;Y时不填
    busi_type = ""
    # 场景类型
    scene_type = ""
    # 证照图片
    license_pic = ""
    # 证照编号
    license_code = ""
    # 证照有效期类型
    license_validity_type = ""
    # 证照有效期开始日期
    license_begin_date = ""
    # 证照有效期截止日期格式：yyyyMMdd。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20220125&lt;/font&gt;&lt;br/&gt;  当license_validity_type&#x3D;0时必填；当license_validity_type&#x3D;1时为空；当use_head_info_flag&#x3D;Y时不填
    license_end_date = ""
    # 成立时间
    found_date = ""
    # 注册资本保留两位小数；条件选填，国营企业、私营企业、外资企业、事业单位、其他、集体经济必填，政府机构、个体工商户可为空；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：100.00&lt;/font&gt;
    reg_capital = ""
    # 注册区
    reg_district_id = ""
    # 注册详细地址
    reg_detail = ""
    # 经营区
    district_id = ""
    # 经营详细地址scene_type&#x3D;OFFLINE/ALL时必填；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：上海市徐汇区XX路XX号&lt;/font&gt;
    detail_addr = ""
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
    # 法人证件有效期截止日期日期格式：yyyyMMdd， &lt;font color&#x3D;&quot;green&quot;&gt;示例值：20220125&lt;/font&gt;&lt;br/&gt;当legal_cert_validity_type&#x3D;0时必填；&lt;br/&gt;当legal_cert_validity_type&#x3D;1时为空；&lt;br/&gt;当use_head_info_flag&#x3D;Y时不填
    legal_cert_end_date = ""
    # 法人证件地址
    legal_addr = ""
    # 法人身份证国徽面
    legal_cert_back_pic = ""
    # 法人身份证人像面
    legal_cert_front_pic = ""
    # 联系人手机号
    contact_mobile_no = ""
    # 联系人电子邮箱
    contact_email = ""
    # 管理员账号
    login_name = ""
    # 开户许可证企业商户需要，结算账号为对公账户必填；通过[图片上传接口](https://paas.huifu.com/open/doc/api/#/shgl/shjj/api_shjj_shtpsc)上传材料；文件类型：F08；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    reg_acct_pic = ""
    # 基本存款账户编号或核准号条件选填；当use_head_info_flag&#x3D;Y时不填 ；&lt;br/&gt;基本存款账户信息请填写基本存款账户编号；开户许可证请填写核准号。&lt;br/&gt;当注册地址或经营地址为如下地区时必填：江苏省、浙江省、湖南省、湖北省、云南省、贵州省、陕西省、河南省、吉林省、黑龙江省、福建省、海南省、重庆市、青海省、宁夏回族自治区；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：J2900123456789&lt;/font&gt;
    open_licence_no = ""
    # 银行卡信息配置
    card_info = ""
    # 银行卡卡号面**对私必填**。通过[图片上传接口](https://paas.huifu.com/open/doc/api/#/shgl/shjj/api_shjj_shtpsc)上传材料；文件类型：F13；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    settle_card_front_pic = ""
    # 持卡人身份证国徽面**对私必填**。通过[图片上传接口](https://paas.huifu.com/open/doc/api/#/shgl/shjj/api_shjj_shtpsc)上传材料；文件类型：F56；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    settle_cert_back_pic = ""
    # 持卡人身份证人像面**对私必填**。通过[图片上传接口](https://paas.huifu.com/open/doc/api/#/shgl/shjj/api_shjj_shtpsc)上传材料；文件类型：F55；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    settle_cert_front_pic = ""
    # 授权委托书**对私非法人、对公非同名结算必填**；通过[图片上传接口](https://paas.huifu.com/open/doc/api/#/shgl/shjj/api_shjj_shtpsc)上传材料；文件类型：F15；开通银行电子账户（中信E管家）需提供F520；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    auth_entrust_pic = ""
    # 上级汇付Id如果head_office_flag&#x3D;0，则字段必填，如果head_office_flag&#x3D;1，上级汇付Id不可传&lt;br/&gt;如果headOfficeFlag&#x3D;0，useHeadInfoFlag&#x3D;Y,且head_huifu_id不为空则基本信息部分复用上级的基本信息。&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：6666000123123123&lt;/font&gt;
    head_huifu_id = ""
    # 商户ICP备案编号商户ICP备案编号或网站许可证号；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：沪ICP备06046402号-28 &lt;/font&gt;&lt;br/&gt;类型为PC网站时，且为企业商户，且开通快捷或网银，或大额转账，或余额支付或分账业务（20%（不含）-100%），或为个人商户开通分账业务（10%（不含）-100%），必填
    mer_icp = ""
    # 店铺门头照
    store_header_pic = ""
    # 店铺内景/工作区域照
    store_indoor_pic = ""
    # 店铺收银台/公司前台照
    store_cashier_desk_pic = ""

    def post(self, extend_infos):
        """
        企业商户进件

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "upper_huifu_id":self.upper_huifu_id,
            "reg_name":self.reg_name,
            "short_name":self.short_name,
            "receipt_name":self.receipt_name,
            "ent_type":self.ent_type,
            "mcc":self.mcc,
            "busi_type":self.busi_type,
            "scene_type":self.scene_type,
            "license_pic":self.license_pic,
            "license_code":self.license_code,
            "license_validity_type":self.license_validity_type,
            "license_begin_date":self.license_begin_date,
            "license_end_date":self.license_end_date,
            "found_date":self.found_date,
            "reg_capital":self.reg_capital,
            "reg_district_id":self.reg_district_id,
            "reg_detail":self.reg_detail,
            "district_id":self.district_id,
            "detail_addr":self.detail_addr,
            "legal_name":self.legal_name,
            "legal_cert_type":self.legal_cert_type,
            "legal_cert_no":self.legal_cert_no,
            "legal_cert_validity_type":self.legal_cert_validity_type,
            "legal_cert_begin_date":self.legal_cert_begin_date,
            "legal_cert_end_date":self.legal_cert_end_date,
            "legal_addr":self.legal_addr,
            "legal_cert_back_pic":self.legal_cert_back_pic,
            "legal_cert_front_pic":self.legal_cert_front_pic,
            "contact_mobile_no":self.contact_mobile_no,
            "contact_email":self.contact_email,
            "login_name":self.login_name,
            "reg_acct_pic":self.reg_acct_pic,
            "open_licence_no":self.open_licence_no,
            "card_info":self.card_info,
            "settle_card_front_pic":self.settle_card_front_pic,
            "settle_cert_back_pic":self.settle_cert_back_pic,
            "settle_cert_front_pic":self.settle_cert_front_pic,
            "auth_entrust_pic":self.auth_entrust_pic,
            "head_huifu_id":self.head_huifu_id,
            "mer_icp":self.mer_icp,
            "store_header_pic":self.store_header_pic,
            "store_indoor_pic":self.store_indoor_pic,
            "store_cashier_desk_pic":self.store_cashier_desk_pic
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BASICDATA_ENT, required_params)
