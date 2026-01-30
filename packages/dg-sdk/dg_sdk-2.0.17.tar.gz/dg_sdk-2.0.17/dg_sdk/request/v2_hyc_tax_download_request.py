from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_HYC_TAX_DOWNLOAD



class V2HycTaxDownloadRequest(object):
    """
    完税凭证下载
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付id
    huifu_id = ""
    # 附件编号
    tax_id = ""

    def post(self, extend_infos):
        """
        完税凭证下载

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "tax_id":self.tax_id
        }
        required_params.update(extend_infos)
        return request_post(V2_HYC_TAX_DOWNLOAD, required_params)
