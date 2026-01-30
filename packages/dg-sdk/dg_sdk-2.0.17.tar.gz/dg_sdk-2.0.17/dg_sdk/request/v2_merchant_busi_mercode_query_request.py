from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_MERCODE_QUERY



class V2MerchantBusiMercodeQueryRequest(object):
    """
    商户微信支付宝ID查询
    """

    # 汇付ID
    huifu_id = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 入驻通道类型
    pay_way = ""

    def post(self, extend_infos):
        """
        商户微信支付宝ID查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "pay_way":self.pay_way
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_MERCODE_QUERY, required_params)
