from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_LGWX_SURROGATE



class V2TradeLgwxSurrogateRequest(object):
    """
    灵工微信代发
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 出款方商户号
    huifu_id = ""
    # 支付金额(元)
    cash_amt = ""
    # 代发模式
    salary_modle_type = ""
    # 落地公司商户号
    bmember_id = ""
    # 子商户应用ID
    sub_appid = ""
    # 异步通知地址
    notify_url = ""
    # 分账明细
    acct_split_bunch = ""

    def post(self, extend_infos):
        """
        灵工微信代发

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "cash_amt":self.cash_amt,
            "salary_modle_type":self.salary_modle_type,
            "bmember_id":self.bmember_id,
            "sub_appid":self.sub_appid,
            "notify_url":self.notify_url,
            "acct_split_bunch":self.acct_split_bunch
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_LGWX_SURROGATE, required_params)
