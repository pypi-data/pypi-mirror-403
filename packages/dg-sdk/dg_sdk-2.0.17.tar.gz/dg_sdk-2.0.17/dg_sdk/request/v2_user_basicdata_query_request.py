from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_USER_BASICDATA_QUERY



class V2UserBasicdataQueryRequest(object):
    """
    用户信息查询
    """

    # 汇付客户Id
    huifu_id = ""
    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""

    def post(self, extend_infos):
        """
        用户信息查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "huifu_id":self.huifu_id,
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date
        }
        required_params.update(extend_infos)
        return request_post(V2_USER_BASICDATA_QUERY, required_params)
