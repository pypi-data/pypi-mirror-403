from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_MODIFY_BUSISTATUS



class V2MerchantBusiModifyBusistatusRequest(object):
    """
    商户状态变更
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 汇付客户Id
    huifu_id = ""
    # 状态
    status = ""
    # 状态变更原因
    upd_status_reason = ""

    def post(self, extend_infos):
        """
        商户状态变更

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "status":self.status,
            "upd_status_reason":self.upd_status_reason
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_MODIFY_BUSISTATUS, required_params)
