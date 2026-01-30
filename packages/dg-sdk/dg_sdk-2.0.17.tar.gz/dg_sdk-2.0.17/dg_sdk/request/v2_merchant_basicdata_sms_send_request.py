from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BASICDATA_SMS_SEND



class V2MerchantBasicdataSmsSendRequest(object):
    """
    商户短信发送
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 手机号verify_type&#x3D;&#39;elecAcctSign&#39;时，手机号为空，系统自动取联系人手机号; &lt;font color&#x3D;&quot;green&quot;&gt;示例值：13911111111&lt;/font&gt;
    phone = ""
    # 验证类型
    verify_type = ""
    # 操作类型verify_type&#x3D;&#39;elecAcctSign&#39;时必填；枚举值：sendSmsCode-发送验证码；identitySmsCode-验证码核实；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：sendSmsCode&lt;/font&gt;
    operation_type = ""
    # 验证码verify_type&#x3D;&#39;elecAcctSign&#39;且operation_type&#x3D;&#39;identitySmsCode&#39;时必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：123456&lt;/font&gt;
    verify_code = ""
    # 中信签约流水号verify_type&#x3D;&#39;elecAcctSign&#39;且operation_type&#x3D;&#39;identitySmsCode&#39;时必填；值为中信E管家签约发送短信时返回值；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：EMSSBPG2504284593690058431260676&lt;/font&gt;
    elec_acct_sign_seq_id = ""

    def post(self, extend_infos):
        """
        商户短信发送

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "phone":self.phone,
            "verify_type":self.verify_type,
            "operation_type":self.operation_type,
            "verify_code":self.verify_code,
            "elec_acct_sign_seq_id":self.elec_acct_sign_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BASICDATA_SMS_SEND, required_params)
