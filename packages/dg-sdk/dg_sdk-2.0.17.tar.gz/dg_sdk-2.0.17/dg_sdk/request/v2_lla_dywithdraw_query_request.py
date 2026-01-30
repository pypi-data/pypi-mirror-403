from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LLA_DYWITHDRAW_QUERY



class V2LlaDywithdrawQueryRequest(object):
    """
    提现记录查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 代运营汇付id
    agency_huifu_id = ""
    # 商家汇付id
    merchant_huifu_id = ""
    # 平台
    platform_type = ""
    # 提现发起开始日期
    start_date = ""
    # 查询游标
    cursor = ""
    # 页大小
    size = ""

    def post(self, extend_infos):
        """
        提现记录查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "agency_huifu_id":self.agency_huifu_id,
            "merchant_huifu_id":self.merchant_huifu_id,
            "platform_type":self.platform_type,
            "start_date":self.start_date,
            "cursor":self.cursor,
            "size":self.size
        }
        required_params.update(extend_infos)
        return request_post(V2_LLA_DYWITHDRAW_QUERY, required_params)
