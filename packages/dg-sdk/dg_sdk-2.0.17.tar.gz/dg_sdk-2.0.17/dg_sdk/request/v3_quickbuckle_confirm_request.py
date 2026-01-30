from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V3_QUICKBUCKLE_CONFIRM



class V3QuickbuckleConfirmRequest(object):
    """
    快捷绑卡确认接口
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 汇付商户Id
    huifu_id = ""
    # 原申请流水号
    org_req_seq_id = ""
    # 原申请日期
    org_req_date = ""
    # 验证码
    verify_code = ""

    def post(self, extend_infos):
        """
        快捷绑卡确认接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "org_req_seq_id":self.org_req_seq_id,
            "org_req_date":self.org_req_date,
            "verify_code":self.verify_code
        }
        required_params.update(extend_infos)
        return request_post(V3_QUICKBUCKLE_CONFIRM, required_params)
