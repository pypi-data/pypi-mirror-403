from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BASICDATA_MODIFY



class V2MerchantBasicdataModifyRequest(object):
    """
    商户基本信息修改
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 直属渠道号
    upper_huifu_id = ""
    # 汇付客户Id
    huifu_id = ""
    # 签约人jsonObject格式；agreement_info中选择电子签约时必填；个人商户填本人信息。
    sign_user_info = ""

    def post(self, extend_infos):
        """
        商户基本信息修改

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "upper_huifu_id":self.upper_huifu_id,
            "huifu_id":self.huifu_id,
            "sign_user_info":self.sign_user_info
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BASICDATA_MODIFY, required_params)
