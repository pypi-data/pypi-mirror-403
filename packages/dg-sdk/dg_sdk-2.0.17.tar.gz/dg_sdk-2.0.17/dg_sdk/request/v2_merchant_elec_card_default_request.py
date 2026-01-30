from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_ELEC_CARD_DEFAULT



class V2MerchantElecCardDefaultRequest(object):
    """
    电子账户设置默认卡
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付Id
    huifu_id = ""
    # 银行卡号
    card_no = ""

    def post(self, extend_infos):
        """
        电子账户设置默认卡

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
        return request_post(V2_MERCHANT_ELEC_CARD_DEFAULT, required_params)
