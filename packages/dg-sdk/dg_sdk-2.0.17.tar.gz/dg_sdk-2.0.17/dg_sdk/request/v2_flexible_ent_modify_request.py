from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_FLEXIBLE_ENT_MODIFY



class V2FlexibleEntModifyRequest(object):
    """
    灵工企业商户业务修改
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付id
    huifu_id = ""
    # 渠道商汇付ID
    upper_huifu_id = ""
    # 商户基本信息jsonObject格式；其中的contact_info和legal_info联系人和法人信息可能在卡信息修改时需要
    basic_info = ""
    # 签约人jsonObject格式 ；协议类型&#x3D;电子合同时，必填；
    sign_user_info = ""

    def post(self, extend_infos):
        """
        灵工企业商户业务修改

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "upper_huifu_id":self.upper_huifu_id,
            "basic_info":self.basic_info,
            "sign_user_info":self.sign_user_info
        }
        required_params.update(extend_infos)
        return request_post(V2_FLEXIBLE_ENT_MODIFY, required_params)
