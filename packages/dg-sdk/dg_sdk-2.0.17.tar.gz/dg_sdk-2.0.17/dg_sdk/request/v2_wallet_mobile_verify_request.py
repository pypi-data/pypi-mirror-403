from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_MOBILE_VERIFY



class V2WalletMobileVerifyRequest(object):
    """
    钱包绑定手机号验证
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 钱包用户ID斗拱系统生成的钱包用户ID。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：6666000123122343&lt;/font&gt;&lt;br/&gt;验证类型为2-密码修改和3-密码重置时，必须提供钱包用户的汇付ID。
    user_huifu_id = ""
    # 用户手机号
    mobile_no = ""
    # 验证类型
    type = ""

    def post(self, extend_infos):
        """
        钱包绑定手机号验证

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "user_huifu_id":self.user_huifu_id,
            "mobile_no":self.mobile_no,
            "type":self.type
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_MOBILE_VERIFY, required_params)
