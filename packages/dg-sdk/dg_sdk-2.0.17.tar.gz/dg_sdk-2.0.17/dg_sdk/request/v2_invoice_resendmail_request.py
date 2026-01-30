from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_INVOICE_RESENDMAIL



class V2InvoiceResendmailRequest(object):
    """
    发票邮件重发接口
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 发票号码
    ivc_number = ""
    # 重发邮箱地址
    mail_addr = ""

    def post(self, extend_infos):
        """
        发票邮件重发接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "ivc_number":self.ivc_number,
            "mail_addr":self.mail_addr
        }
        required_params.update(extend_infos)
        return request_post(V2_INVOICE_RESENDMAIL, required_params)
