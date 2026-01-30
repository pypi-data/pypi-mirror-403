from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LINKAPP_AUTH_RESULT



class V2LinkappAuthResultRequest(object):
    """
    授权结果查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 平台类型
    platform_type = ""
    # 授权请求ID
    auth_seq_id = ""

    def post(self, extend_infos):
        """
        授权结果查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "platform_type":self.platform_type,
            "auth_seq_id":self.auth_seq_id
        }
        required_params.update(extend_infos)
        return request_post(V2_LINKAPP_AUTH_RESULT, required_params)
