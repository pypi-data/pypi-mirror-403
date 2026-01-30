from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_INVOICE_PERMISSION_GRANT



class V2InvoicePermissionGrantRequest(object):
    """
    电子发票业务开通
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 开票方汇付ID
    huifu_id = ""
    # 开通类型
    status = ""

    def post(self, extend_infos):
        """
        电子发票业务开通

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "status":self.status
        }
        required_params.update(extend_infos)
        return request_post(V2_INVOICE_PERMISSION_GRANT, required_params)
