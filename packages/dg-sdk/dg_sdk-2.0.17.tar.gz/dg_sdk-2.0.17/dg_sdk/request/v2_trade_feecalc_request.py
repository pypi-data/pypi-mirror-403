from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_FEECALC



class V2TradeFeecalcRequest(object):
    """
    手续费试算
    """

    # 商户号
    huifu_id = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 交易类型
    trade_type = ""
    # 交易金额
    trans_amt = ""

    def post(self, extend_infos):
        """
        手续费试算

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "trade_type":self.trade_type,
            "trans_amt":self.trans_amt
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_FEECALC, required_params)
