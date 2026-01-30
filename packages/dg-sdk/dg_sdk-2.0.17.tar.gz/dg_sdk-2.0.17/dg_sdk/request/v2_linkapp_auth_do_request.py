from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LINKAPP_AUTH_DO



class V2LinkappAuthDoRequest(object):
    """
    商户公域授权
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 平台类型
    platform_type = ""
    # 协议地址
    contract_url = ""
    # 签约商户名称
    contract_mer_name = ""
    # 签约时间
    contract_time = ""
    # 登录用手机号第一次登录有需要手机验证码的情况;（需要授权手机安装一个转发短信的应用）
    phone_number = ""
    # 商户类型商户类型：0个人店 1企业 2个体工商户 3其他(目前固定填3即可)
    merchant_type = ""

    def post(self, extend_infos):
        """
        商户公域授权

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "platform_type":self.platform_type,
            "contract_url":self.contract_url,
            "contract_mer_name":self.contract_mer_name,
            "contract_time":self.contract_time,
            "phone_number":self.phone_number,
            "merchant_type":self.merchant_type
        }
        required_params.update(extend_infos)
        return request_post(V2_LINKAPP_AUTH_DO, required_params)
