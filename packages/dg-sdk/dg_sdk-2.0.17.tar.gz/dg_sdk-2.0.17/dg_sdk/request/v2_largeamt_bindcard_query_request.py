from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LARGEAMT_BINDCARD_QUERY



class V2LargeamtBindcardQueryRequest(object):
    """
    银行大额支付绑卡查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 银行卡号密文
    card_no = ""
    # 每页条数
    page_size = ""
    # 分页页码
    page_num = ""

    def post(self, extend_infos):
        """
        银行大额支付绑卡查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "card_no":self.card_no,
            "page_size":self.page_size,
            "page_num":self.page_num
        }
        required_params.update(extend_infos)
        return request_post(V2_LARGEAMT_BINDCARD_QUERY, required_params)
