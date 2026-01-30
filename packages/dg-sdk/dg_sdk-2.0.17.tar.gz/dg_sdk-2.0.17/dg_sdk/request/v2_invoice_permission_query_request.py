from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_INVOICE_PERMISSION_QUERY



class V2InvoicePermissionQueryRequest(object):
    """
    电子发票业务开通查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 是否包含下级
    include_sub_flag = ""
    # 当前页
    page_num = ""
    # 分页大小
    page_size = ""

    def post(self, extend_infos):
        """
        电子发票业务开通查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "include_sub_flag":self.include_sub_flag,
            "page_num":self.page_num,
            "page_size":self.page_size
        }
        required_params.update(extend_infos)
        return request_post(V2_INVOICE_PERMISSION_QUERY, required_params)
