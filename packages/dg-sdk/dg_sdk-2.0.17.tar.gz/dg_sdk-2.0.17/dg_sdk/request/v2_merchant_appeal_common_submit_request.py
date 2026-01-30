from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_APPEAL_COMMON_SUBMIT



class V2MerchantAppealCommonSubmitRequest(object):
    """
    提交申诉
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户经营模式
    business_pattern = ""
    # 协查单号
    assist_id = ""
    # 申诉单号
    appeal_id = ""
    # 商户类型
    mer_type = ""
    # 申诉人姓名
    appeal_person_name = ""
    # 申诉人身份证号
    appeal_person_cert_no = ""
    # 申诉人联系电话
    appeal_person_phone_no = ""
    # 法人姓名
    legal_name = ""
    # 法人身份证号
    legal_cert_no = ""
    # 法人联系电话
    legal_phone_no = ""
    # 商户主营业务
    main_business = ""
    # 申诉理由
    appeal_desc = ""

    def post(self, extend_infos):
        """
        提交申诉

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "business_pattern":self.business_pattern,
            "assist_id":self.assist_id,
            "appeal_id":self.appeal_id,
            "mer_type":self.mer_type,
            "appeal_person_name":self.appeal_person_name,
            "appeal_person_cert_no":self.appeal_person_cert_no,
            "appeal_person_phone_no":self.appeal_person_phone_no,
            "legal_name":self.legal_name,
            "legal_cert_no":self.legal_cert_no,
            "legal_phone_no":self.legal_phone_no,
            "main_business":self.main_business,
            "appeal_desc":self.appeal_desc
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_APPEAL_COMMON_SUBMIT, required_params)
