from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BASICDATA_INDV



class V2MerchantBasicdataIndvRequest(object):
    """
    个人商户进件
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 直属渠道号
    upper_huifu_id = ""
    # 商户名
    reg_name = ""
    # 所属行业
    mcc = ""
    # 场景类型
    scene_type = ""
    # 经营区
    district_id = ""
    # 经营详细地址scene_type字段含有线下场景时必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：上海市徐汇区XX路XX号&lt;/font&gt;
    detail_addr = ""
    # 负责人证件号码
    legal_cert_no = ""
    # 负责人证件有效期开始日期
    legal_cert_begin_date = ""
    # 负责人证件有效期截止日期
    legal_cert_end_date = ""
    # 负责人身份证地址
    legal_addr = ""
    # 负责人身份证国徽面
    legal_cert_back_pic = ""
    # 负责人身份证人像面
    legal_cert_front_pic = ""
    # 负责人手机号
    contact_mobile_no = ""
    # 负责人电子邮箱
    contact_email = ""
    # 结算卡信息配置
    card_info = ""
    # 银行卡卡号面
    settle_card_front_pic = ""
    # 商户ICP备案编号商户ICP备案编号或网站许可证号；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：沪ICP备06046402号-28 &lt;/font&gt;&lt;br/&gt;类型为PC网站时，且为企业商户，且开通快捷或网银，或大额转账，或余额支付或分账业务（20%（不含）-100%），或为个人商户开通分账业务（10%（不含）-100%），必填
    mer_icp = ""
    # 店铺门头照文件类型：F22；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;&lt;br/&gt;微信/支付宝实名认证个人商户，门头照也使用此字段； &lt;br/&gt;门店场所：提交门店门口照片，要求招牌清晰可见; &lt;br/&gt;小微商户流动经营/便民服务：提交经营/服务现场照片
    store_header_pic = ""
    # 店铺内景/工作区域照文件类型：F24；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;&lt;br/&gt;微信/支付宝实名认证个人商户，内景照也使用此字段； &lt;br/&gt;门店场所：提交店内环境照片 &lt;br/&gt;小微商户流动经营/便民服务：可提交另一张经营/服务现场照片
    store_indoor_pic = ""
    # 店铺收银台/公司前台照商户线下场景需要提供；文件类型：F105；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    store_cashier_desk_pic = ""
    # 上级商户汇付ID如果head_office_flag&#x3D;0，则字段必填&lt;font color&#x3D;&quot;green&quot;&gt;示例值：6666000123123123&lt;/font&gt;
    head_huifu_id = ""

    def post(self, extend_infos):
        """
        个人商户进件

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "upper_huifu_id":self.upper_huifu_id,
            "reg_name":self.reg_name,
            "mcc":self.mcc,
            "scene_type":self.scene_type,
            "district_id":self.district_id,
            "detail_addr":self.detail_addr,
            "legal_cert_no":self.legal_cert_no,
            "legal_cert_begin_date":self.legal_cert_begin_date,
            "legal_cert_end_date":self.legal_cert_end_date,
            "legal_addr":self.legal_addr,
            "legal_cert_back_pic":self.legal_cert_back_pic,
            "legal_cert_front_pic":self.legal_cert_front_pic,
            "contact_mobile_no":self.contact_mobile_no,
            "contact_email":self.contact_email,
            "card_info":self.card_info,
            "settle_card_front_pic":self.settle_card_front_pic,
            "mer_icp":self.mer_icp,
            "store_header_pic":self.store_header_pic,
            "store_indoor_pic":self.store_indoor_pic,
            "store_cashier_desk_pic":self.store_cashier_desk_pic,
            "head_huifu_id":self.head_huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BASICDATA_INDV, required_params)
