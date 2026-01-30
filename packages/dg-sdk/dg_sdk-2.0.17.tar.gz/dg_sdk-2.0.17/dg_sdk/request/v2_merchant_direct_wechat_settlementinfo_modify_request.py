from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_WECHAT_SETTLEMENTINFO_MODIFY



class V2MerchantDirectWechatSettlementinfoModifyRequest(object):
    """
    微信直连-修改微信结算帐号
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付ID
    huifu_id = ""
    # 开发者的应用ID
    app_id = ""
    # 微信商户号
    mch_id = ""
    # 特约商户号
    sub_mchid = ""
    # 账户类型
    account_type = ""
    # 开户银行
    account_bank = ""
    # 开户银行省市编码
    bank_address_code = ""
    # 银行账号
    account_number = ""

    def post(self, extend_infos):
        """
        微信直连-修改微信结算帐号

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "app_id":self.app_id,
            "mch_id":self.mch_id,
            "sub_mchid":self.sub_mchid,
            "account_type":self.account_type,
            "account_bank":self.account_bank,
            "bank_address_code":self.bank_address_code,
            "account_number":self.account_number
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_WECHAT_SETTLEMENTINFO_MODIFY, required_params)
