from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYAFTERUSE_INSTALLMENT_CREATE



class V2TradePayafteruseInstallmentCreateRequest(object):
    """
    分期单创建
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 分期金额
    fq_amt = ""

    def post(self, extend_infos):
        """
        分期单创建

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "fq_amt":self.fq_amt
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYAFTERUSE_INSTALLMENT_CREATE, required_params)
