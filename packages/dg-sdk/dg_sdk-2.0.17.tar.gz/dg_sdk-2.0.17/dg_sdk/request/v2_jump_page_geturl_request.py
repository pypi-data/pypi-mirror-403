from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_JUMP_PAGE_GETURL



class V2JumpPageGeturlRequest(object):
    """
    获取控台页面跳转链接
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 外部系统用户标识
    external_user_id = ""
    # 功能菜单
    jump_function_type = ""

    def post(self, extend_infos):
        """
        获取控台页面跳转链接

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "external_user_id":self.external_user_id,
            "jump_function_type":self.jump_function_type
        }
        required_params.update(extend_infos)
        return request_post(V2_JUMP_PAGE_GETURL, required_params)
