from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_HEAD_CONFIG



class V2MerchantBusiHeadConfigRequest(object):
    """
    开通下级商户权限配置接口
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付客户Id
    huifu_id = ""
    # 产品编号
    product_id = ""
    # 直属渠道号
    upper_huifu_id = ""

    def post(self, extend_infos):
        """
        开通下级商户权限配置接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "product_id":self.product_id,
            "upper_huifu_id":self.upper_huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_HEAD_CONFIG, required_params)
