from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_SETTLE_MODIFY



class V2MerchantSettleModifyRequest(object):
    """
    修改子账户配置
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 上级汇付Id
    upper_huifu_id = ""
    # 子账户号
    acct_id = ""
    # 结算规则配置
    settle_config = ""
    # 结算卡信息配置新账户绑定的结算银行账户。jsonObject格式。若结算规则中上送token_no，则card_info不填。
    card_info = ""

    def post(self, extend_infos):
        """
        修改子账户配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "upper_huifu_id":self.upper_huifu_id,
            "acct_id":self.acct_id,
            "settle_config":self.settle_config,
            "card_info":self.card_info
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_SETTLE_MODIFY, required_params)
