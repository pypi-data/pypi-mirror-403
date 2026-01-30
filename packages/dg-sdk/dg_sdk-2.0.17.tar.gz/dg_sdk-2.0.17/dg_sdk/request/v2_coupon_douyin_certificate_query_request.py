from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_COUPON_DOUYIN_CERTIFICATE_QUERY



class V2CouponDouyinCertificateQueryRequest(object):
    """
    抖音券状态批量查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 门店绑定流水号
    bind_id = ""
    # 验券准备接口返回的加密券码encrypted_code和order_id二选一必传，encrypted_code和order_id不能同时传入
    encrypted_code = ""
    # 订单id验券准备等接口获得，encrypted_code和order_id二选一必传，encrypted_code和order_id不能同时传入
    order_id = ""

    def post(self, extend_infos):
        """
        抖音券状态批量查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bind_id":self.bind_id,
            "encrypted_code":self.encrypted_code,
            "order_id":self.order_id
        }
        required_params.update(extend_infos)
        return request_post(V2_COUPON_DOUYIN_CERTIFICATE_QUERY, required_params)
