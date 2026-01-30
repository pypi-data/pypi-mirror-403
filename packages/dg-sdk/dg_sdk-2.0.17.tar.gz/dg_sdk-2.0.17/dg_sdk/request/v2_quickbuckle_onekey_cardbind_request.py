from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_QUICKBUCKLE_ONEKEY_CARDBIND



class V2QuickbuckleOnekeyCardbindRequest(object):
    """
    一键绑卡
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付Id
    huifu_id = ""
    # 顾客用户号 
    out_cust_id = ""
    # 银行号
    bank_id = ""
    # 银行卡开户姓名 
    card_name = ""
    # 银行卡绑定身份证
    cert_id = ""
    # 银行卡绑定证件类型
    cert_type = ""
    # 证件有效期到期日长期有效不填.格式：yyyyMMdd。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20311111&lt;/font&gt;
    cert_end_date = ""
    # 银行卡绑定手机号 
    card_mp = ""
    # 卡的借贷类型
    dc_type = ""
    # 异步请求地址
    async_return_url = ""
    # 设备信息域
    trx_device_inf = ""

    def post(self, extend_infos):
        """
        一键绑卡

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "out_cust_id":self.out_cust_id,
            "bank_id":self.bank_id,
            "card_name":self.card_name,
            "cert_id":self.cert_id,
            "cert_type":self.cert_type,
            "cert_end_date":self.cert_end_date,
            "card_mp":self.card_mp,
            "dc_type":self.dc_type,
            "async_return_url":self.async_return_url,
            "trx_device_inf":self.trx_device_inf
        }
        required_params.update(extend_infos)
        return request_post(V2_QUICKBUCKLE_ONEKEY_CARDBIND, required_params)
