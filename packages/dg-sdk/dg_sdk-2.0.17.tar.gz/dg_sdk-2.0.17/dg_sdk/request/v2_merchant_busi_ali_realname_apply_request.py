from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_ALI_REALNAME_APPLY



class V2MerchantBusiAliRealnameApplyRequest(object):
    """
    支付宝实名申请提交
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付ID
    huifu_id = ""
    # 主体信息
    auth_identity_info = ""
    # 联系人信息
    contact_person_info = ""

    def post(self, extend_infos):
        """
        支付宝实名申请提交

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "auth_identity_info":self.auth_identity_info,
            "contact_person_info":self.contact_person_info
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_ALI_REALNAME_APPLY, required_params)
