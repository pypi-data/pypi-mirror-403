class PaymentRefundRequest(object):
    """
    交易退款请求类
    """
    
    # 必填参数
    req_date = ""  # 请求日期，长度8，格式yyyyMMdd
    req_seq_id = ""  # 请求流水号，长度128
    huifu_id = ""  # 商户号，长度32
    ord_amt = ""  # 申请退款金额，长度14，单位元，保留两位小数
    org_req_date = ""  # 原交易请求日期，长度8，格式yyyyMMdd
    
    # 条件必填参数（三选一）
    org_hf_seq_id = ""  # 原交易全局流水号，长度128
    org_party_order_id = ""  # 原交易微信支付宝的商户单号，长度64
    org_req_seq_id = ""  # 原交易请求流水号，长度128
    
    # 可选参数
    remark = ""  # 备注，长度84
    notify_url = ""  # 异步通知地址，长度512
    tx_metadata = ""  # 扩展参数集合，jsonObject字符串
    
    def combileParams(self):
        """
        组合请求参数
        :return: 参数字典
        """
        required_params = {
            "req_date": self.req_date,
            "req_seq_id": self.req_seq_id,
            "huifu_id": self.huifu_id,
            "ord_amt": self.ord_amt,
            "org_req_date": self.org_req_date
        }
        
        # 检查条件必填参数（三选一）
        query_params = []
        if self.org_hf_seq_id:
            query_params.append("org_hf_seq_id")
            required_params["org_hf_seq_id"] = self.org_hf_seq_id
            
        if self.org_party_order_id:
            query_params.append("org_party_order_id")
            required_params["org_party_order_id"] = self.org_party_order_id
            
        if self.org_req_seq_id:
            query_params.append("org_req_seq_id")
            required_params["org_req_seq_id"] = self.org_req_seq_id
        
        # 验证至少有一个查询参数
        if len(query_params) == 0:
            raise ValueError("必须提供以下参数之一：org_hf_seq_id, org_party_order_id, org_req_seq_id")
        
        # 添加可选参数
        optional_params = {
            "remark": self.remark,
            "notify_url": self.notify_url,
            "tx_metadata": self.tx_metadata
        }
        
        for key, value in optional_params.items():
            if value:
                required_params[key] = value
                
        return required_params