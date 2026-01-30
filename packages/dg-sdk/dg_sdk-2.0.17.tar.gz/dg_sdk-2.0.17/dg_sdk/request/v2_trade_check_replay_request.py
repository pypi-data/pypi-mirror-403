from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_CHECK_REPLAY



class V2TradeCheckReplayRequest(object):
    """
    交易结算对账文件重新生成
    """

    # 请求流水号
    req_seq_id = ""
    # 交易日期
    req_date = ""
    # 汇付机构编号
    huifu_id = ""
    # 文件类型
    file_type = ""

    def post(self, extend_infos):
        """
        交易结算对账文件重新生成

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "file_type":self.file_type
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_CHECK_REPLAY, required_params)
