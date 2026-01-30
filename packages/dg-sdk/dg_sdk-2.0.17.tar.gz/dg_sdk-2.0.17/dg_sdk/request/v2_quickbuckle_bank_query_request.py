from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_QUICKBUCKLE_BANK_QUERY



class V2QuickbuckleBankQueryRequest(object):
    """
    银行列表查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 业务类型
    biz_type = ""
    # 借贷类型
    dc_type = ""

    def post(self, extend_infos):
        """
        银行列表查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "biz_type":self.biz_type,
            "dc_type":self.dc_type
        }
        required_params.update(extend_infos)
        return request_post(V2_QUICKBUCKLE_BANK_QUERY, required_params)
