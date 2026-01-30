from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_SETTLE_CONFIG



class V2MerchantSettleConfigRequest(object):
    """
    子账户开通配置
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 上级汇付Id
    upper_huifu_id = ""
    # 子账户类型
    acct_type = ""
    # 账户名称
    acct_name = ""
    # 结算卡信息配置新账户绑定的结算银行账户。jsonObject格式。若结算规则中上送token_no，则card_info不填。
    card_info = ""

    def post(self, extend_infos):
        """
        子账户开通配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "upper_huifu_id":self.upper_huifu_id,
            "acct_type":self.acct_type,
            "acct_name":self.acct_name,
            "card_info":self.card_info
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_SETTLE_CONFIG, required_params)
