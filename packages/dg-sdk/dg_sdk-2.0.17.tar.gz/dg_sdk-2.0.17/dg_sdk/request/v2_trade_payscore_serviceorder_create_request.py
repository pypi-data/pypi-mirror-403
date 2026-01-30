from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYSCORE_SERVICEORDER_CREATE



class V2TradePayscoreServiceorderCreateRequest(object):
    """
    创建支付分
    """

    # 请求日期
    req_date = ""
    # 商户申请单号
    req_seq_id = ""
    # 汇付商户号
    huifu_id = ""
    # 服务信息
    service_introduction = ""
    # 服务风险金
    risk_fund = ""
    # 服务时间
    time_range = ""
    # 商户回调地址
    notify_url = ""

    def post(self, extend_infos):
        """
        创建支付分

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "service_introduction":self.service_introduction,
            "risk_fund":self.risk_fund,
            "time_range":self.time_range,
            "notify_url":self.notify_url
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYSCORE_SERVICEORDER_CREATE, required_params)
