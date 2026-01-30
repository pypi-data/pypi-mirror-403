from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_QUICKBUCKLE_QUERY



class V2QuickbuckleQueryRequest(object):
    """
    快捷绑卡查询
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 汇付商户Id
    huifu_id = ""
    # 用户id
    out_cust_id = ""

    def post(self, extend_infos):
        """
        快捷绑卡查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "out_cust_id":self.out_cust_id
        }
        required_params.update(extend_infos)
        return request_post(V2_QUICKBUCKLE_QUERY, required_params)
