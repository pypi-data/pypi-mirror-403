from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_USER_BASICDATA_INDV_MODIFY



class V2UserBasicdataIndvModifyRequest(object):
    """
    个人用户基本信息修改
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付客户Id
    huifu_id = ""

    def post(self, extend_infos):
        """
        个人用户基本信息修改

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_USER_BASICDATA_INDV_MODIFY, required_params)
