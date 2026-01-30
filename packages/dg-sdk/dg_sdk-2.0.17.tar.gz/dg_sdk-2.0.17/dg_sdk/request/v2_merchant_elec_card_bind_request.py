from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_ELEC_CARD_BIND



class V2MerchantElecCardBindRequest(object):
    """
    电子账户绑卡
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付Id
    huifu_id = ""
    # 电子卡信息
    elec_card_info = ""

    def post(self, extend_infos):
        """
        电子账户绑卡

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "elec_card_info":self.elec_card_info
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_ELEC_CARD_BIND, required_params)
