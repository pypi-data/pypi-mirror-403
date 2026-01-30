from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PREAUTH



class V2TradePreauthRequest(object):
    """
    微信支付宝预授权
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号
    huifu_id = ""
    # 交易金额
    trans_amt = ""
    # 商品描述
    goods_desc = ""
    # 支付授权码
    auth_code = ""
    # 安全信息
    risk_check_data = ""

    def post(self, extend_infos):
        """
        微信支付宝预授权

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "trans_amt":self.trans_amt,
            "goods_desc":self.goods_desc,
            "auth_code":self.auth_code,
            "risk_check_data":self.risk_check_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PREAUTH, required_params)
