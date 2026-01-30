from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_UNIONSIGN



class V2TradeOnlinepaymentUnionsignRequest(object):
    """
    银联统一在线收银台签约接口
    """

    # 商户号
    huifu_id = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 支付场景
    pay_scene = ""
    # 异步通知地址
    notify_url = ""
    # 设备信息
    terminal_device_data = ""
    # 三方支付数据jsonObject；&lt;br/&gt;
    third_pay_data = ""

    def post(self, extend_infos):
        """
        银联统一在线收银台签约接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "pay_scene":self.pay_scene,
            "notify_url":self.notify_url,
            "terminal_device_data":self.terminal_device_data,
            "third_pay_data":self.third_pay_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_UNIONSIGN, required_params)
