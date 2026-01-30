from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_PASSWORD_RESET



class V2WalletPasswordResetRequest(object):
    """
    钱包密码重置
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 钱包用户ID
    user_huifu_id = ""
    # 钱包绑定手机号
    cust_mobile = ""
    # 手机短信验证码
    verify_no = ""
    # 短信验证流水号
    verify_seq_id = ""
    # 跳转地址
    front_url = ""

    def post(self, extend_infos):
        """
        钱包密码重置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "user_huifu_id":self.user_huifu_id,
            "cust_mobile":self.cust_mobile,
            "verify_no":self.verify_no,
            "verify_seq_id":self.verify_seq_id,
            "front_url":self.front_url
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_PASSWORD_RESET, required_params)
