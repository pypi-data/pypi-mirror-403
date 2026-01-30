from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_UNIONPAY



class V2TradeOnlinepaymentUnionpayRequest(object):
    """
    银联统一在线收银台
    """

    # 商户号
    huifu_id = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 订单金额
    trans_amt = ""
    # 商品描述
    order_desc = ""
    # 安全信息
    risk_check_data = ""
    # 三方支付数据jsonObject&lt;br/&gt;pay_scene&#x3D;U_JSAPI或pay_scene&#x3D;U_MINIAPP时，必填
    third_pay_data = ""

    def post(self, extend_infos):
        """
        银联统一在线收银台

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "trans_amt":self.trans_amt,
            "order_desc":self.order_desc,
            "risk_check_data":self.risk_check_data,
            "third_pay_data":self.third_pay_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_UNIONPAY, required_params)
