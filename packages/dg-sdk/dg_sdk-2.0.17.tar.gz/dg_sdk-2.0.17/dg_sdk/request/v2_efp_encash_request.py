from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_EFP_ENCASH



class V2EfpEncashRequest(object):
    """
    全渠道资金提现申请
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付id
    huifu_id = ""
    # 交易金额.单位:元，2位小数
    cash_amt = ""
    # 取现卡序列号
    token_no = ""

    def post(self, extend_infos):
        """
        全渠道资金提现申请

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "cash_amt":self.cash_amt,
            "token_no":self.token_no
        }
        required_params.update(extend_infos)
        return request_post(V2_EFP_ENCASH, required_params)
