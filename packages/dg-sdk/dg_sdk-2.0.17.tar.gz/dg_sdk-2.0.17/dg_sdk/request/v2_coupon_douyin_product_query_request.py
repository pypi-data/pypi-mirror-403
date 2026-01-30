from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_COUPON_DOUYIN_PRODUCT_QUERY



class V2CouponDouyinProductQueryRequest(object):
    """
    抖音套餐映射接口
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 门店绑定流水号
    bind_id = ""

    def post(self, extend_infos):
        """
        抖音套餐映射接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bind_id":self.bind_id
        }
        required_params.update(extend_infos)
        return request_post(V2_COUPON_DOUYIN_PRODUCT_QUERY, required_params)
