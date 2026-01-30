from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYSCORE_DEDUCT_REGITSTER



class V2TradePayscoreDeductRegitsterRequest(object):
    """
    登记扣款信息
    """

    # 请求日期
    req_date = ""
    # 商户申请单号
    req_seq_id = ""
    # 汇付商户号
    huifu_id = ""

    def post(self, extend_infos):
        """
        登记扣款信息

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYSCORE_DEDUCT_REGITSTER, required_params)
