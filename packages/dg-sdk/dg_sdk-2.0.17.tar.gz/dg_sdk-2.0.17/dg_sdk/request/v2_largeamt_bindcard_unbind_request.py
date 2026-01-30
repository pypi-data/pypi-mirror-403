from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LARGEAMT_BINDCARD_UNBIND



class V2LargeamtBindcardUnbindRequest(object):
    """
    银行大额支付解绑
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 银行卡号密文
    card_no = ""

    def post(self, extend_infos):
        """
        银行大额支付解绑

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "card_no":self.card_no
        }
        required_params.update(extend_infos)
        return request_post(V2_LARGEAMT_BINDCARD_UNBIND, required_params)
