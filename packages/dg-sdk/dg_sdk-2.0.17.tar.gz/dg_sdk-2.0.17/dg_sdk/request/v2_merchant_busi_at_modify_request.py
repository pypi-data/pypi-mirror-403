from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_AT_MODIFY



class V2MerchantBusiAtModifyRequest(object):
    """
    微信支付宝入驻信息修改
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # AT信息修改列表
    at_reg_list = ""

    def post(self, extend_infos):
        """
        微信支付宝入驻信息修改

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "at_reg_list":self.at_reg_list
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_AT_MODIFY, required_params)
