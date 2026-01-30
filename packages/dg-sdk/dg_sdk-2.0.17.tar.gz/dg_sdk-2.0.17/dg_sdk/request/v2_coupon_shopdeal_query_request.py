from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_COUPON_SHOPDEAL_QUERY



class V2CouponShopdealQueryRequest(object):
    """
    美团非餐饮获取团购信息
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 门店绑定流水号
    bind_id = ""
    # 页码
    offset = ""
    # 页大小
    limit = ""
    # 售卖平台
    source = ""

    def post(self, extend_infos):
        """
        美团非餐饮获取团购信息

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bind_id":self.bind_id,
            "offset":self.offset,
            "limit":self.limit,
            "source":self.source
        }
        required_params.update(extend_infos)
        return request_post(V2_COUPON_SHOPDEAL_QUERY, required_params)
