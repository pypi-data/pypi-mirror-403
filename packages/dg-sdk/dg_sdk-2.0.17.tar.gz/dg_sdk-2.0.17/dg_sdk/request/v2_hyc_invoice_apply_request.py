from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_HYC_INVOICE_APPLY



class V2HycInvoiceApplyRequest(object):
    """
    申请开票
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付id
    huifu_id = ""
    # 开票类目
    invoice_category = ""
    # 汇付全局流水号集合
    hf_seq_ids = ""

    def post(self, extend_infos):
        """
        申请开票

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "invoice_category":self.invoice_category,
            "hf_seq_ids":self.hf_seq_ids
        }
        required_params.update(extend_infos)
        return request_post(V2_HYC_INVOICE_APPLY, required_params)
