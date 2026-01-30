from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_CREATE



class V2WalletCreateRequest(object):
    """
    钱包开户
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 个人姓名钱包账户开户人的本人真实姓名；wallet_type&#x3D;1时必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：张三&lt;/font&gt;
    name = ""
    # 钱包绑定手机号
    mobile_no = ""
    # 手机短信验证码
    verify_code = ""
    # 短信验证流水号
    verify_seq_id = ""
    # 跳转地址
    front_url = ""

    def post(self, extend_infos):
        """
        钱包开户

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "name":self.name,
            "mobile_no":self.mobile_no,
            "verify_code":self.verify_code,
            "verify_seq_id":self.verify_seq_id,
            "front_url":self.front_url
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_CREATE, required_params)
