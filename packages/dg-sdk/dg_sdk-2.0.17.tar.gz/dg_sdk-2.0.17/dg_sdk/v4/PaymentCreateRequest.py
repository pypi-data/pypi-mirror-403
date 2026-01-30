class PaymentCreateRequest(object):
    """
    聚合支付创建请求类
    """
    
    # 必填参数
    req_seq_id = ""  # 请求流水号，长度128
    huifu_id = ""    # 商户号，长度32
    trade_type = ""  # 交易类型，长度16
    trans_amt = ""   # 交易金额，长度14
    goods_desc = ""  # 商品描述，长度128
    method_expand = ""  # 交易类型扩展参数，jsonObject字符串
    
    # 条件必填参数
    tx_metadata = ""  # 扩展参数集合，交易能力扩展
    
    # 可选参数
    req_date = ""  # 请求日期，长度8，格式yyyyMMdd
    remark = ""    # 备注，长度255
    acct_id = ""   # 账户号，长度9
    time_expire = ""  # 交易有效期，长度14，格式yyyyMMddHHmmss
    delay_acct_flag = ""  # 延迟标识，长度1，Y/N
    fee_flag = ""  # 手续费扣款标识，长度1，1:外扣 2:内扣
    limit_pay_type = ""  # 禁用支付方式，长度128
    channel_no = ""  # 渠道号，长度32
    pay_scene = ""  # 场景类型，长度2
    term_div_coupon_type = ""  # 传入分帐遇到优惠的处理规则，长度2，1:按比例分,2:按分账明细顺序保障,3:只给交易商户
    fq_mer_discount_flag = ""  # 商户贴息标记，长度1，Y:商户全额贴息，P:商户部分贴息
    notify_url = ""  # 异步通知地址，长度504
    
    def combileParams(self):
        """
        组合请求参数
        :return: 参数字典
        """
        required_params = {
            "req_seq_id": self.req_seq_id,
            "huifu_id": self.huifu_id,
            "trade_type": self.trade_type,
            "trans_amt": self.trans_amt,
            "goods_desc": self.goods_desc,
            "method_expand": self.method_expand
        }
        
        # 添加条件必填参数
        if self.tx_metadata:
            required_params["tx_metadata"] = self.tx_metadata
            
        # 添加可选参数
        optional_params = {
            "req_date": self.req_date,
            "remark": self.remark,
            "acct_id": self.acct_id,
            "time_expire": self.time_expire,
            "delay_acct_flag": self.delay_acct_flag,
            "fee_flag": self.fee_flag,
            "limit_pay_type": self.limit_pay_type,
            "channel_no": self.channel_no,
            "pay_scene": self.pay_scene,
            "term_div_coupon_type": self.term_div_coupon_type,
            "fq_mer_discount_flag": self.fq_mer_discount_flag,
            "notify_url": self.notify_url
        }
        
        # 只添加非空的可选参数
        for key, value in optional_params.items():
            if value:
                required_params[key] = value
                
        return required_params