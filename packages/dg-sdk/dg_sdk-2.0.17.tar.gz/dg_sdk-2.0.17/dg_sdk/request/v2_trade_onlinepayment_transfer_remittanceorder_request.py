from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_TRANSFER_REMITTANCEORDER



class V2TradeOnlinepaymentTransferRemittanceorderRequest(object):
    """
    汇付入账查询
    """

    # 商户号
    huifu_id = ""
    # 原请求开始日期
    org_req_start_date = ""
    # 原请求结束日期
    org_req_end_date = ""

    def post(self, extend_infos):
        """
        汇付入账查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "org_req_start_date":self.org_req_start_date,
            "org_req_end_date":self.org_req_end_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_TRANSFER_REMITTANCEORDER, required_params)
