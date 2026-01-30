from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_USER_LIST_QUERY



class V2UserListQueryRequest(object):
    """
    用户列表查询
    """

    # 法人证件号
    legal_cert_no = ""
    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""

    def post(self, extend_infos):
        """
        用户列表查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "legal_cert_no":self.legal_cert_no,
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_USER_LIST_QUERY, required_params)
