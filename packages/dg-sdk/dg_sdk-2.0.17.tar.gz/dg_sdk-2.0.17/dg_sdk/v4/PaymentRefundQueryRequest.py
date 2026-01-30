class PaymentRefundQueryRequest(object):
    """
    退款查询请求类
    """
    
    # 必填参数
    huifu_id = ""  # 商户号，长度32
    
    # 条件必填参数（三选一）
    org_hf_seq_id = ""  # 退款全局流水号，长度128
    org_req_seq_id = ""  # 退款请求流水号，长度128
    mer_ord_id = ""  # 终端订单号，长度50
    
    # 可选参数
    org_req_date = ""  # 退款请求日期，长度8，格式yyyyMMdd
    
    def combileParams(self):
        """
        组合请求参数
        :return: 参数字典
        """
        required_params = {
            "huifu_id": self.huifu_id
        }
        
        # 检查条件必填参数（三选一）
        query_params = []
        if self.org_hf_seq_id:
            query_params.append("org_hf_seq_id")
            required_params["org_hf_seq_id"] = self.org_hf_seq_id
            
        if self.org_req_seq_id:
            query_params.append("org_req_seq_id")
            required_params["org_req_seq_id"] = self.org_req_seq_id
            
        if self.mer_ord_id:
            query_params.append("mer_ord_id")
            required_params["mer_ord_id"] = self.mer_ord_id
        
        # 验证至少有一个查询参数
        if len(query_params) == 0:
            raise ValueError("必须提供以下参数之一：org_hf_seq_id, org_req_seq_id, mer_ord_id")
        
        # 添加可选参数
        if self.org_req_date:
            required_params["org_req_date"] = self.org_req_date
                
        return required_params