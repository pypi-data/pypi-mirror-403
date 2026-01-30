from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V3_QUICKBUCKLE_APPLY



class V3QuickbuckleApplyRequest(object):
    """
    快捷绑卡申请接口
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 汇付客户Id
    huifu_id = ""
    # 商户用户id
    out_cust_id = ""
    # 银行卡号
    card_no = ""
    # 银行卡开户姓名
    card_name = ""
    # 银行卡绑定身份证
    cert_no = ""
    # 个人证件有效期类型
    cert_validity_type = ""
    # 个人证件有效期起始日
    cert_begin_date = ""
    # 个人证件有效期到期日长期有效不填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20420905&lt;/font&gt;
    cert_end_date = ""
    # 银行卡绑定手机号
    mobile_no = ""
    # 挂网协议编号授权信息(招行绑卡需要上送)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：34463343&lt;/font&gt;
    protocol_no = ""

    def post(self, extend_infos):
        """
        快捷绑卡申请接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "out_cust_id":self.out_cust_id,
            "card_no":self.card_no,
            "card_name":self.card_name,
            "cert_no":self.cert_no,
            "cert_validity_type":self.cert_validity_type,
            "cert_begin_date":self.cert_begin_date,
            "cert_end_date":self.cert_end_date,
            "mobile_no":self.mobile_no,
            "protocol_no":self.protocol_no
        }
        required_params.update(extend_infos)
        return request_post(V3_QUICKBUCKLE_APPLY, required_params)
