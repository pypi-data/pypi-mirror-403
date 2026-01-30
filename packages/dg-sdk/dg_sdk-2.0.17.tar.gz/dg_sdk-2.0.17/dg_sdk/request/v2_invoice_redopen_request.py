from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_INVOICE_REDOPEN



class V2InvoiceRedopenRequest(object):
    """
    红字发票开具接口
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 原发票号码
    ori_ivc_number = ""
    # 红冲原因
    red_apply_reason = ""
    # 红冲申请来源
    red_apply_source = ""

    def post(self, extend_infos):
        """
        红字发票开具接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "ori_ivc_number":self.ori_ivc_number,
            "red_apply_reason":self.red_apply_reason,
            "red_apply_source":self.red_apply_source
        }
        required_params.update(extend_infos)
        return request_post(V2_INVOICE_REDOPEN, required_params)
