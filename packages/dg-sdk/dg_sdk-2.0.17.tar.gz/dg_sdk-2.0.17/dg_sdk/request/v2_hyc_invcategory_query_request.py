from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_HYC_INVCATEGORY_QUERY



class V2HycInvcategoryQueryRequest(object):
    """
    开票类目查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 落地公司机构号
    minor_agent_id = ""
    # 商户号lg_platform_type为HXY或空时必填
    huifu_id = ""

    def post(self, extend_infos):
        """
        开票类目查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "minor_agent_id":self.minor_agent_id,
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_HYC_INVCATEGORY_QUERY, required_params)
