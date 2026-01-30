from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_INVOICE_MER_VERIFYCODE_UPLOAD



class V2InvoiceMerVerifycodeUploadRequest(object):
    """
    上传短信验证码
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 开票方汇付ID
    huifu_id = ""
    # 校验类型
    verify_type = ""
    # 流水号
    serial_num = ""
    # 验证码
    verify_code = ""

    def post(self, extend_infos):
        """
        上传短信验证码

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "verify_type":self.verify_type,
            "serial_num":self.serial_num,
            "verify_code":self.verify_code
        }
        required_params.update(extend_infos)
        return request_post(V2_INVOICE_MER_VERIFYCODE_UPLOAD, required_params)
