from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_USER_BUSI_OPEN



class V2UserBusiOpenRequest(object):
    """
    用户业务入驻
    """

    # 汇付ID
    huifu_id = ""
    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 渠道商/商户汇付Id
    upper_huifu_id = ""
    # 乐接活配置当合作平台为乐接活，必填
    ljh_data = ""
    # 汇薪云配置当合作平台为汇薪云，必填
    hxy_data = ""

    def post(self, extend_infos):
        """
        用户业务入驻

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "upper_huifu_id":self.upper_huifu_id,
            "ljh_data":self.ljh_data,
            "hxy_data":self.hxy_data
        }
        required_params.update(extend_infos)
        return request_post(V2_USER_BUSI_OPEN, required_params)
