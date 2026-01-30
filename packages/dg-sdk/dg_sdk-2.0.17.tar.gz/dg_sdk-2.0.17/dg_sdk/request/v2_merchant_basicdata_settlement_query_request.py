from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BASICDATA_SETTLEMENT_QUERY



class V2MerchantBasicdataSettlementQueryRequest(object):
    """
    结算记录查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付客户Id
    huifu_id = ""
    # 结算开始日期
    begin_date = ""
    # 结算结束日期
    end_date = ""
    # 分页条数
    page_size = ""

    def post(self, extend_infos):
        """
        结算记录查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "begin_date":self.begin_date,
            "end_date":self.end_date,
            "page_size":self.page_size
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BASICDATA_SETTLEMENT_QUERY, required_params)
