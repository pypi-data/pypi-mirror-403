from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_COUPON_MEITUAN_QUERY



class V2CouponMeituanQueryRequest(object):
    """
    美团卡券核销结果查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 门店绑定流水号
    bind_id = ""
    # 券码
    receipt_code = ""

    def post(self, extend_infos):
        """
        美团卡券核销结果查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bind_id":self.bind_id,
            "receipt_code":self.receipt_code
        }
        required_params.update(extend_infos)
        return request_post(V2_COUPON_MEITUAN_QUERY, required_params)
