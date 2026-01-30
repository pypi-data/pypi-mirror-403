from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_OCO_ORDER_LIST



class V2OcoOrderListRequest(object):
    """
    全渠道订单分账查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 分账数据源
    busi_source = ""
    # 交易时间
    trans_date = ""
    # 页码
    page_num = ""
    # 每页大小
    page_size = ""

    def post(self, extend_infos):
        """
        全渠道订单分账查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "busi_source":self.busi_source,
            "trans_date":self.trans_date,
            "page_num":self.page_num,
            "page_size":self.page_size
        }
        required_params.update(extend_infos)
        return request_post(V2_OCO_ORDER_LIST, required_params)
