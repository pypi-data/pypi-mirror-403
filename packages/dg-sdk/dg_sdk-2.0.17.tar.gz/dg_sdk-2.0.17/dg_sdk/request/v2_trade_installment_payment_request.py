from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_INSTALLMENT_PAYMENT



class V2TradeInstallmentPaymentRequest(object):
    """
    分期支付
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号
    huifu_id = ""
    # 交易金额
    trans_amt = ""
    # 分期数
    installment_num = ""
    # 商品描述
    goods_desc = ""
    # 安全信息
    risk_check_data = ""
    # 京东白条分期信息trans_type&#x3D;JDBT时，必填jsonObject字符串，京东白条分期相关信息通过该参数集上送
    jdbt_data = ""
    # 银联聚分期信息trans_type&#x3D;YLJFQ-银联聚分期时，必填jsonObject字符串，银联聚分期相关信息通过该参数集上送
    yljfq_data = ""

    def post(self, extend_infos):
        """
        分期支付

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "trans_amt":self.trans_amt,
            "installment_num":self.installment_num,
            "goods_desc":self.goods_desc,
            "risk_check_data":self.risk_check_data,
            "jdbt_data":self.jdbt_data,
            "yljfq_data":self.yljfq_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_INSTALLMENT_PAYMENT, required_params)
