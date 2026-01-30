from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ONLINEPAYMENT_TRANSFER_BANKMISTAKE_APPLY



class V2TradeOnlinepaymentTransferBankmistakeApplyRequest(object):
    """
    银行大额支付差错申请
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 交易金额
    trans_amt = ""
    # 订单类型
    order_type = ""
    # 原请求流水号当bank_mode&#x3D;BFJ，order_flag&#x3D;Y时，必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2022012514120615009&lt;/font&gt;
    org_req_seq_id = ""
    # 原请求日期当bank_mode&#x3D;BFJ，order_flag&#x3D;Y时，必填，格式:yyyyMMdd；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20220125&lt;/font&gt;
    org_req_date = ""
    # 异步通知地址
    notify_url = ""

    def post(self, extend_infos):
        """
        银行大额支付差错申请

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "trans_amt":self.trans_amt,
            "order_type":self.order_type,
            "org_req_seq_id":self.org_req_seq_id,
            "org_req_date":self.org_req_date,
            "notify_url":self.notify_url
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ONLINEPAYMENT_TRANSFER_BANKMISTAKE_APPLY, required_params)
