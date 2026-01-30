from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_URL_FORWARD



class V2MerchantUrlForwardRequest(object):
    """
    商户统一进件（页面版）
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 渠道商号
    upper_huifu_id = ""
    # 门店号
    store_id = ""

    def post(self, extend_infos):
        """
        商户统一进件（页面版）

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "upper_huifu_id":self.upper_huifu_id,
            "store_id":self.store_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_URL_FORWARD, required_params)
