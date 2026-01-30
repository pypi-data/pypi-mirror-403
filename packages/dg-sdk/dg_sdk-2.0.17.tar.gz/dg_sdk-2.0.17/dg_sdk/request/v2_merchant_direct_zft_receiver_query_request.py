from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_ZFT_RECEIVER_QUERY



class V2MerchantDirectZftReceiverQueryRequest(object):
    """
    直付通分账关系查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付ID
    huifu_id = ""
    # 开发者的应用ID
    app_id = ""
    # 每页数目
    page_size = ""
    # 页数
    page_num = ""

    def post(self, extend_infos):
        """
        直付通分账关系查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "app_id":self.app_id,
            "page_size":self.page_size,
            "page_num":self.page_num
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_ZFT_RECEIVER_QUERY, required_params)
