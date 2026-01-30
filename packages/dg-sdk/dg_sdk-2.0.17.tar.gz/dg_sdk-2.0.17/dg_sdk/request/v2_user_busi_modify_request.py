from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_USER_BUSI_MODIFY



class V2UserBusiModifyRequest(object):
    """
    用户业务入驻修改
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付ID
    huifu_id = ""
    # 乐接活配置当合作平台为乐接活，必填
    ljh_data = ""
    # 签约人信息当电子回单配置开关为开通时必填
    sign_user_info = ""
    # 汇薪云配置当合作平台为汇薪云时，该参数必填
    hxy_data = ""

    def post(self, extend_infos):
        """
        用户业务入驻修改

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "ljh_data":self.ljh_data,
            "sign_user_info":self.sign_user_info,
            "hxy_data":self.hxy_data
        }
        required_params.update(extend_infos)
        return request_post(V2_USER_BUSI_MODIFY, required_params)
