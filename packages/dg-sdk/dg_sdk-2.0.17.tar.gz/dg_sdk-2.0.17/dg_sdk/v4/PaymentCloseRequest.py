class PaymentCloseRequest(object):
    """
    交易关单请求类
    """
    
    # 必填参数
    req_date = ""  # 请求日期，长度8，格式yyyyMMdd
    req_seq_id = ""  # 请求流水号，长度128
    huifu_id = ""  # 商户号，长度32
    org_req_date = ""  # 原交易请求日期，长度8，格式yyyyMMdd
    
    # 条件必填参数（二选一）
    org_hf_seq_id = ""  # 原交易返回的全局流水号，长度128
    org_req_seq_id = ""  # 原交易请求流水号，长度128
    
    def combileParams(self):
        """
        组合请求参数
        :return: 参数字典
        """
        required_params = {
            "req_date": self.req_date,
            "req_seq_id": self.req_seq_id,
            "huifu_id": self.huifu_id,
            "org_req_date": self.org_req_date
        }
        
        # 检查条件必填参数（二选一）
        if self.org_hf_seq_id and self.org_req_seq_id:
            raise ValueError("org_hf_seq_id 和 org_req_seq_id 只能提供一个")
        
        if self.org_hf_seq_id:
            required_params["org_hf_seq_id"] = self.org_hf_seq_id
        elif self.org_req_seq_id:
            required_params["org_req_seq_id"] = self.org_req_seq_id
        else:
            raise ValueError("必须提供以下参数之一：org_hf_seq_id, org_req_seq_id")
                
        return required_params