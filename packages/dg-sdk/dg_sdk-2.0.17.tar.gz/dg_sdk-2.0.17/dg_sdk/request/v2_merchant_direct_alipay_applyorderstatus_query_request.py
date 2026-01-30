from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_ALIPAY_APPLYORDERSTATUS_QUERY



class V2MerchantDirectAlipayApplyorderstatusQueryRequest(object):
    """
    支付宝直连-查询申请状态
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 开发者的应用ID
    app_id = ""

    def post(self, extend_infos):
        """
        支付宝直连-查询申请状态

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "app_id":self.app_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_ALIPAY_APPLYORDERSTATUS_QUERY, required_params)
