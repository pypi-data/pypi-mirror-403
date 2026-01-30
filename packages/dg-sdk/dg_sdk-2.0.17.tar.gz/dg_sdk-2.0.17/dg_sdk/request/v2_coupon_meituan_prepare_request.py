from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_COUPON_MEITUAN_PREPARE



class V2CouponMeituanPrepareRequest(object):
    """
    美团卡券校验
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 团购券码
    coupon_code = ""
    # 门店绑定流水号
    bind_id = ""

    def post(self, extend_infos):
        """
        美团卡券校验

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "coupon_code":self.coupon_code,
            "bind_id":self.bind_id
        }
        required_params.update(extend_infos)
        return request_post(V2_COUPON_MEITUAN_PREPARE, required_params)
