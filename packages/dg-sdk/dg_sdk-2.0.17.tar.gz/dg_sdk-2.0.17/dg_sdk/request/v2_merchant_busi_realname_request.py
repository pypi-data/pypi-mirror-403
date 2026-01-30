from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_REALNAME



class V2MerchantBusiRealnameRequest(object):
    """
    微信实名认证
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付ID
    huifu_id = ""
    # 联系人姓名
    name = ""
    # 联系人手机号
    mobile = ""
    # 联系人身份证号码
    id_card_number = ""
    # 联系人类型
    contact_type = ""

    def post(self, extend_infos):
        """
        微信实名认证

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "name":self.name,
            "mobile":self.mobile,
            "id_card_number":self.id_card_number,
            "contact_type":self.contact_type
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_REALNAME, required_params)
