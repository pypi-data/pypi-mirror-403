from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYMENT_ZXE_UNKNOWNINCOME_DISPOSE



class V2TradePaymentZxeUnknownincomeDisposeRequest(object):
    """
    不明来账处理
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 银行侧交易流水号参照异步通知里的bank_serial_no；&lt;br/&gt;“银行侧交易流水号”和“来账银行账号，来账账户名称，交易金额，交易日期”二选一必填。
    bank_serial_no = ""
    # 来账银行账号需要密文传输，使用汇付RSA公钥加密(加密前64位，加密后最长2048位），参见[参考文档](https://paas.huifu.com/open/doc/guide/#/api_jiami_jiemi)；示例值：Ly+fnExeyPOTzfOtgRRur77nJB9TAe4PGgK9M……fc6XJXZss&#x3D;“银行侧交易流水号”和“来账银行账号，来账账户名称，交易金额，交易日期”二选一必填。
    pay_acct = ""
    # 来账账户名称“银行侧交易流水号”和“来账银行账号，来账账户名称，交易金额，交易日期”二选一必填。
    pay_acct_name = ""
    # 交易金额“银行侧交易流水号”和“来账银行账号，来账账户名称，交易金额，交易日期”二选一必填。
    trans_amt = ""
    # 交易日期“银行侧交易流水号”和“来账银行账号，来账账户名称，交易金额，交易日期”二选一必填。
    trans_date = ""
    # 操作类型
    operate_type = ""

    def post(self, extend_infos):
        """
        不明来账处理

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bank_serial_no":self.bank_serial_no,
            "pay_acct":self.pay_acct,
            "pay_acct_name":self.pay_acct_name,
            "trans_amt":self.trans_amt,
            "trans_date":self.trans_date,
            "operate_type":self.operate_type
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYMENT_ZXE_UNKNOWNINCOME_DISPOSE, required_params)
