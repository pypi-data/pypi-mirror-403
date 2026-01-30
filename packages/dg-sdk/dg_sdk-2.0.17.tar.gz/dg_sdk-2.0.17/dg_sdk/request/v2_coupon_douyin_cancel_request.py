from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_COUPON_DOUYIN_CANCEL



class V2CouponDouyinCancelRequest(object):
    """
    抖音卡券撤销
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 门店绑定流水号
    bind_id = ""
    # 抖音券码
    encrypted_code = ""
    # 核销标识
    verify_id = ""

    def post(self, extend_infos):
        """
        抖音卡券撤销

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bind_id":self.bind_id,
            "encrypted_code":self.encrypted_code,
            "verify_id":self.verify_id
        }
        required_params.update(extend_infos)
        return request_post(V2_COUPON_DOUYIN_CANCEL, required_params)
