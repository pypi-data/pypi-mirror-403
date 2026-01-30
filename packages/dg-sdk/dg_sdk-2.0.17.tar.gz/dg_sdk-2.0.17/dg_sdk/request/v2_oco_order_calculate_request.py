from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_OCO_ORDER_CALCULATE



class V2OcoOrderCalculateRequest(object):
    """
    全渠道订单分账计算
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 分账数据源
    busi_source = ""
    # 业务订单号
    oco_order_id = ""

    def post(self, extend_infos):
        """
        全渠道订单分账计算

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "busi_source":self.busi_source,
            "oco_order_id":self.oco_order_id
        }
        required_params.update(extend_infos)
        return request_post(V2_OCO_ORDER_CALCULATE, required_params)
