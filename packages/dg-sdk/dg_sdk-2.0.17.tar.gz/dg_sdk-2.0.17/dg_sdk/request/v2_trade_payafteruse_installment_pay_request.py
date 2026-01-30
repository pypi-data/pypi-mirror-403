from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYAFTERUSE_INSTALLMENT_PAY



class V2TradePayafteruseInstallmentPayRequest(object):
    """
    分期扣款
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 客户号
    huifu_id = ""
    # 交易金额
    trans_amt = ""
    # 商品描述
    goods_desc = ""
    # 风控信息
    risk_check_data = ""
    # 支付宝扩展参数集合
    alipay_data = ""

    def post(self, extend_infos):
        """
        分期扣款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "trans_amt":self.trans_amt,
            "goods_desc":self.goods_desc,
            "risk_check_data":self.risk_check_data,
            "alipay_data":self.alipay_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYAFTERUSE_INSTALLMENT_PAY, required_params)
