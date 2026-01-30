class PaymentQueryRequest(object):
    """
    支付订单查询请求类
    """
    
    # 必填参数
    huifu_id = ""  # 汇付商户号，长度32
    
    # 条件必填参数（三选一）
    out_ord_id = ""  # 汇付服务订单号，长度32
    hf_seq_id = ""   # 创建服务订单返回的汇付全局流水号，长度128
    req_seq_id = ""  # 服务订单创建请求流水号，长度128
    
    # 可选参数
    req_date = ""  # 请求日期，长度8，格式yyyyMMdd
    
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
        if self.out_ord_id:
            query_params.append("out_ord_id")
            required_params["out_ord_id"] = self.out_ord_id
            
        if self.hf_seq_id:
            query_params.append("hf_seq_id")
            required_params["hf_seq_id"] = self.hf_seq_id
            
        if self.req_seq_id:
            query_params.append("req_seq_id")
            required_params["req_seq_id"] = self.req_seq_id
        
        # 验证至少有一个查询参数
        if len(query_params) == 0:
            raise ValueError("必须提供以下参数之一：out_ord_id, hf_seq_id, req_seq_id")
        
        # 添加可选参数
        if self.req_date:
            required_params["req_date"] = self.req_date
                
        return required_params