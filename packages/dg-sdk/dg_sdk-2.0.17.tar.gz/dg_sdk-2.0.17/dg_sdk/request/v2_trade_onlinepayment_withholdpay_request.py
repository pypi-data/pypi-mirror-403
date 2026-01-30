from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_WITHHOLDPAY



class V2TradeOnlinepaymentWithholdpayRequest(object):
    """
    代扣支付
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号
    huifu_id = ""
    # 用户客户号
    user_huifu_id = ""
    # 绑卡id
    card_bind_id = ""
    # 订单金额
    trans_amt = ""
    # 商品描述
    goods_desc = ""
    # 代扣类型
    withhold_type = ""
    # 异步通知地址
    notify_url = ""
    # 银行扩展数据
    extend_pay_data = ""
    # 风控信息
    risk_check_data = ""
    # 设备信息数据
    terminal_device_data = ""

    def post(self, extend_infos):
        """
        代扣支付

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "user_huifu_id":self.user_huifu_id,
            "card_bind_id":self.card_bind_id,
            "trans_amt":self.trans_amt,
            "goods_desc":self.goods_desc,
            "withhold_type":self.withhold_type,
            "notify_url":self.notify_url,
            "extend_pay_data":self.extend_pay_data,
            "risk_check_data":self.risk_check_data,
            "terminal_device_data":self.terminal_device_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_WITHHOLDPAY, required_params)
