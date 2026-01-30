from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_USER_BASICDATA_ENT



class V2UserBasicdataEntRequest(object):
    """
    企业用户基本信息开户
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 企业用户名称
    reg_name = ""
    # 营业执照编号
    license_code = ""
    # 证照有效期类型
    license_validity_type = ""
    # 证照有效期起始日期
    license_begin_date = ""
    # 证照有效期结束日期日期格式：yyyyMMdd; 非长期有效时必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20320905&lt;/font&gt;
    license_end_date = ""
    # 注册地址(省)
    reg_prov_id = ""
    # 注册地址(市)
    reg_area_id = ""
    # 注册地址(区)
    reg_district_id = ""
    # 注册地址(详细信息)
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
    # 法人证件有效期截止日期日期格式：yyyyMMdd; 非长期有效时必填，长期有效为空；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20320905&lt;/font&gt;
    legal_cert_end_date = ""
    # 法人国籍法人的证件类型为外国人居留证时，必填，参见《[国籍编码](https://cloudpnrcdn.oss-cn-shanghai.aliyuncs.com/opps/api/prod/download_file/area/%E5%9B%BD%E7%B1%8D.xlsx)》&lt;font color&#x3D;&quot;green&quot;&gt;示例值：CHN&lt;/font&gt;
    legal_cert_nationality = ""
    # 联系人姓名
    contact_name = ""
    # 联系人手机号
    contact_mobile = ""
    # 管理员账号如需短信通知则必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：Lg20220222013747&lt;/font&gt;
    login_name = ""

    def post(self, extend_infos):
        """
        企业用户基本信息开户

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "reg_name":self.reg_name,
            "license_code":self.license_code,
            "license_validity_type":self.license_validity_type,
            "license_begin_date":self.license_begin_date,
            "license_end_date":self.license_end_date,
            "reg_prov_id":self.reg_prov_id,
            "reg_area_id":self.reg_area_id,
            "reg_district_id":self.reg_district_id,
            "reg_detail":self.reg_detail,
            "legal_name":self.legal_name,
            "legal_cert_type":self.legal_cert_type,
            "legal_cert_no":self.legal_cert_no,
            "legal_cert_validity_type":self.legal_cert_validity_type,
            "legal_cert_begin_date":self.legal_cert_begin_date,
            "legal_cert_end_date":self.legal_cert_end_date,
            "legal_cert_nationality":self.legal_cert_nationality,
            "contact_name":self.contact_name,
            "contact_mobile":self.contact_mobile,
            "login_name":self.login_name
        }
        required_params.update(extend_infos)
        return request_post(V2_USER_BASICDATA_ENT, required_params)
