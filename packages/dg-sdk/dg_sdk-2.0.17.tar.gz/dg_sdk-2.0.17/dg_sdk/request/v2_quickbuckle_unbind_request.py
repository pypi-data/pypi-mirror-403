from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_QUICKBUCKLE_UNBIND



class V2QuickbuckleUnbindRequest(object):
    """
    新增快捷/代扣解绑接口
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 汇付商户Id
    huifu_id = ""
    # 用户ID
    out_cust_id = ""
    # 卡令牌
    token_no = ""

    def post(self, extend_infos):
        """
        新增快捷/代扣解绑接口

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "out_cust_id":self.out_cust_id,
            "token_no":self.token_no
        }
        required_params.update(extend_infos)
        return request_post(V2_QUICKBUCKLE_UNBIND, required_params)
