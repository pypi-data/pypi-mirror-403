from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_BATCHTRANSLOG_QUERY



class V2TradeBatchtranslogQueryRequest(object):
    """
    批量出金交易查询
    """

    # 商户号
    huifu_id = ""
    # 开始日期
    begin_date = ""
    # 结束日期
    end_date = ""

    def post(self, extend_infos):
        """
        批量出金交易查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "begin_date":self.begin_date,
            "end_date":self.end_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_BATCHTRANSLOG_QUERY, required_params)
