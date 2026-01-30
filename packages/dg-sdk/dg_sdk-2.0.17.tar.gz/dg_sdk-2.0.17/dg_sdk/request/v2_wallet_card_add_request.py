from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_WALLET_CARD_ADD



class V2WalletCardAddRequest(object):
    """
    新增绑定卡
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 钱包用户ID
    user_huifu_id = ""
    # 跳转地址
    front_url = ""
    # 设备信息域
    trx_device_info  = ""

    def post(self, extend_infos):
        """
        新增绑定卡

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "user_huifu_id":self.user_huifu_id,
            "front_url":self.front_url,
            "trx_device_info ":self.trx_device_info 
        }
        required_params.update(extend_infos)
        return request_post(V2_WALLET_CARD_ADD, required_params)
