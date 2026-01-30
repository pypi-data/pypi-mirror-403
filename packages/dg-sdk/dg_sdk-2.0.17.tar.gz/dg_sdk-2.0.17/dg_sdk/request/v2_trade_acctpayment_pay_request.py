from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ACCTPAYMENT_PAY



class V2TradeAcctpaymentPayRequest(object):
    """
    余额支付
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 出款方商户号
    out_huifu_id = ""
    # 支付金额
    ord_amt = ""
    # 分账对象
    acct_split_bunch = ""
    # 安全信息
    risk_check_data = ""
    # 资金类型资金类型。支付渠道为中信E管家时，资金类型必填（[详见说明](https://paas.huifu.com/open/doc/api/#/yuer/api_zxegjzllx)）
    fund_type = ""
    # 手续费承担方标识余额支付手续费承担方标识；商户余额支付扣收规则为接口指定承担方时必填！枚举值：&lt;br/&gt;OUT：出款方；&lt;br/&gt;IN：分账接受方。&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：IN&lt;/font&gt;
    trans_fee_take_flag = ""
    # 核验值verify_type不为空时必填。当verify_type&#x3D;SMS时，填写用户收到的短信验证码
    verify_value = ""

    def post(self, extend_infos):
        """
        余额支付

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "out_huifu_id":self.out_huifu_id,
            "ord_amt":self.ord_amt,
            "acct_split_bunch":self.acct_split_bunch,
            "risk_check_data":self.risk_check_data,
            "fund_type":self.fund_type,
            "trans_fee_take_flag":self.trans_fee_take_flag,
            "verify_value":self.verify_value
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ACCTPAYMENT_PAY, required_params)
