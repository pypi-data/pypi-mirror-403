from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_INVOICE_MER_REG



class V2InvoiceMerRegRequest(object):
    """
    商户注册
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 开票方汇付ID
    huifu_id = ""
    # 纳税人识别号
    tax_payer_id = ""
    # 销方名称
    tax_payer_name = ""
    # 公司电话
    tel_no = ""
    # 公司地址
    reg_address = ""
    # 开户银行
    bank_name = ""
    # 开户账户
    account_no = ""
    # 联系人手机号
    contact_phone_no = ""
    # 开票方式
    open_mode = ""
    # 所属省
    prov_id = ""
    # 所属市
    city_id = ""

    def post(self, extend_infos):
        """
        商户注册

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "tax_payer_id":self.tax_payer_id,
            "tax_payer_name":self.tax_payer_name,
            "tel_no":self.tel_no,
            "reg_address":self.reg_address,
            "bank_name":self.bank_name,
            "account_no":self.account_no,
            "contact_phone_no":self.contact_phone_no,
            "open_mode":self.open_mode,
            "prov_id":self.prov_id,
            "city_id":self.city_id
        }
        required_params.update(extend_infos)
        return request_post(V2_INVOICE_MER_REG, required_params)
