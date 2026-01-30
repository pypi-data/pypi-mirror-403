from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LARGEAMT_BINDCARD_BIND



class V2LargeamtBindcardBindRequest(object):
    """
    银行大额支付绑卡
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 卡类型
    card_type = ""
    # 银行账户名
    card_name = ""
    # 银行卡号密文
    card_no = ""
    # 银行编码
    bank_code = ""
    # 手机号
    mobile_no = ""

    def post(self, extend_infos):
        """
        银行大额支付绑卡

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "card_type":self.card_type,
            "card_name":self.card_name,
            "card_no":self.card_no,
            "bank_code":self.bank_code,
            "mobile_no":self.mobile_no
        }
        required_params.update(extend_infos)
        return request_post(V2_LARGEAMT_BINDCARD_BIND, required_params)
