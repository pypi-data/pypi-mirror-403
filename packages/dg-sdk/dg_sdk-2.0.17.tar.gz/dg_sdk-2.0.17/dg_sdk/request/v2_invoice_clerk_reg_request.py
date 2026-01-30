from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_INVOICE_CLERK_REG



class V2InvoiceClerkRegRequest(object):
    """
    开票员登记
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 开票员登录身份
    clerk_identity = ""
    # 登录账号
    login_account = ""
    # 登录密码
    login_password = ""
    # 开票员手机号
    clerk_phone_no = ""

    def post(self, extend_infos):
        """
        开票员登记

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "clerk_identity":self.clerk_identity,
            "login_account":self.login_account,
            "login_password":self.login_password,
            "clerk_phone_no":self.clerk_phone_no
        }
        required_params.update(extend_infos)
        return request_post(V2_INVOICE_CLERK_REG, required_params)
