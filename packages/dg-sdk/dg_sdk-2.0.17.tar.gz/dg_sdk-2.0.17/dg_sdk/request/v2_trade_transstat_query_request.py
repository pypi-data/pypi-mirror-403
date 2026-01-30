from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_TRANSSTAT_QUERY



class V2TradeTransstatQueryRequest(object):
    """
    批量交易状态查询
    """

    # 商户号
    huifu_id = ""
    # 页码
    page_no = ""
    # 页大小
    page_size = ""
    # 请求日期
    req_date = ""

    def post(self, extend_infos):
        """
        批量交易状态查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "page_no":self.page_no,
            "page_size":self.page_size,
            "req_date":self.req_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_TRANSSTAT_QUERY, required_params)
