from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_QUICKBUCKLE_WITHHOLD_PAGE_GET



class V2QuickbuckleWithholdPageGetRequest(object):
    """
    代扣绑卡页面版
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付Id
    huifu_id = ""
    # 订单号
    order_id = ""
    # 订单日期
    order_date = ""

    def post(self, extend_infos):
        """
        代扣绑卡页面版

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "order_id":self.order_id,
            "order_date":self.order_date
        }
        required_params.update(extend_infos)
        return request_post(V2_QUICKBUCKLE_WITHHOLD_PAGE_GET, required_params)
