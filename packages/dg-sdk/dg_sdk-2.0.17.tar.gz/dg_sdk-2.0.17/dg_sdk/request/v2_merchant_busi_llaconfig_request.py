from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_LLACONFIG



class V2MerchantBusiLlaconfigRequest(object):
    """
    代运营代扣业务配置
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付id
    huifu_id = ""
    # 所属渠道商
    upper_huifu_id = ""
    # 代运营配置json字符串，业务角色为AGENCY:代运营时必填
    lla_agency_config = ""
    # 商家配置json字符串，业务角色为MERCHANT:商家时必填
    lla_merchant_config = ""
    # 纸质协议文件协议类型为纸质且业务角色不为空时必填，文件类型F633；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    paper_agreement_file = ""
    # 签约人信息json字符串，协议类型为电子时必填
    sign_user_info = ""

    def post(self, extend_infos):
        """
        代运营代扣业务配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "upper_huifu_id":self.upper_huifu_id,
            "lla_agency_config":self.lla_agency_config,
            "lla_merchant_config":self.lla_merchant_config,
            "paper_agreement_file":self.paper_agreement_file,
            "sign_user_info":self.sign_user_info
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_LLACONFIG, required_params)
