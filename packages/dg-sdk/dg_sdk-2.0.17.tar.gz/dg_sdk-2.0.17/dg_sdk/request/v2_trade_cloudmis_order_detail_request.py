from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_CLOUDMIS_ORDER_DETAIL



class V2TradeCloudmisOrderDetailRequest(object):
    """
    云MIS订单详情查询接口
    """

    # 请求流水号
    req_id = ""
    # 原MIS请求的交易订单号
    org_third_order_id = ""
    # 原MIS请求商户号
    org_huifu_id = ""
    # 原MIS请求终端号
    org_device_id = ""
    # 原MIS请求日期
    org_req_date = ""

    def post(self, extend_infos):
        """
        云MIS订单详情查询接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_id":self.req_id,
            "org_third_order_id":self.org_third_order_id,
            "org_huifu_id":self.org_huifu_id,
            "org_device_id":self.org_device_id,
            "org_req_date":self.org_req_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_CLOUDMIS_ORDER_DETAIL, required_params)
