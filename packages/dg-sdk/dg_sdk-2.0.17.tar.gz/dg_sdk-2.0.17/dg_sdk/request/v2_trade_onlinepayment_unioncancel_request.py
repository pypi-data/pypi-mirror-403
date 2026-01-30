from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_UNIONCANCEL



class V2TradeOnlinepaymentUnioncancelRequest(object):
    """
    银联统一在线收银台解约接口
    """

    # 商户号
    huifu_id = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 原请求日期
    org_req_date = ""
    # 原请求流水号
    org_req_seq_id = ""
    # 异步通知地址
    notify_url = ""

    def post(self, extend_infos):
        """
        银联统一在线收银台解约接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "notify_url":self.notify_url
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_UNIONCANCEL, required_params)
