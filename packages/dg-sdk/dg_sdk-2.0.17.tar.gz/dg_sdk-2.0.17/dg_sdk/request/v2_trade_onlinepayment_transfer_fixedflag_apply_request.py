from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_TRANSFER_FIXEDFLAG_APPLY



class V2TradeOnlinepaymentTransferFixedflagApplyRequest(object):
    """
    银行大额支付固定转账标识申请接口
    """

    # 商户号
    huifu_id = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 唯一标识号
    unique_no = ""

    def post(self, extend_infos):
        """
        银行大额支付固定转账标识申请接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "unique_no":self.unique_no
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_TRANSFER_FIXEDFLAG_APPLY, required_params)
