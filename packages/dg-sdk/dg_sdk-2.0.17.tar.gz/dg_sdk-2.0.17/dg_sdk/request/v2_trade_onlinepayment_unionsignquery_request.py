from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_UNIONSIGNQUERY



class V2TradeOnlinepaymentUnionsignqueryRequest(object):
    """
    银联统一在线收银台签解约查询接口
    """

    # 汇付商户号
    huifu_id = ""
    # 原请求日期
    org_req_date = ""
    # 原请求流水号
    org_req_seq_id = ""

    def post(self, extend_infos):
        """
        银联统一在线收银台签解约查询接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_UNIONSIGNQUERY, required_params)
