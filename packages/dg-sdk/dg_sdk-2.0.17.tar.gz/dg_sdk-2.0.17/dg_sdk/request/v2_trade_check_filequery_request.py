from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_CHECK_FILEQUERY



class V2TradeCheckFilequeryRequest(object):
    """
    交易结算对账单查询
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 汇付客户Id
    huifu_id = ""
    # 文件生成日期
    file_date = ""

    def post(self, extend_infos):
        """
        交易结算对账单查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "file_date":self.file_date
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_CHECK_FILEQUERY, required_params)
