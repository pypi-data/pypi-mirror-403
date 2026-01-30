from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BASICDATA_STATUS_QUERY



class V2MerchantBasicdataStatusQueryRequest(object):
    """
    申请单状态查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 申请单
    apply_no = ""
    # 汇付客户Id
    huifu_id = ""

    def post(self, extend_infos):
        """
        申请单状态查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "apply_no":self.apply_no,
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BASICDATA_STATUS_QUERY, required_params)
