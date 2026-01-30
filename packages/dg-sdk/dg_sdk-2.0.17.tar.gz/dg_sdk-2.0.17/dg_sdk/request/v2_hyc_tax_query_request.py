from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_HYC_TAX_QUERY



class V2HycTaxQueryRequest(object):
    """
    完税凭证查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付id
    huifu_id = ""
    # 开始时间
    start_date = ""
    # 结束时间
    end_date = ""

    def post(self, extend_infos):
        """
        完税凭证查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "start_date":self.start_date,
            "end_date":self.end_date
        }
        required_params.update(extend_infos)
        return request_post(V2_HYC_TAX_QUERY, required_params)
