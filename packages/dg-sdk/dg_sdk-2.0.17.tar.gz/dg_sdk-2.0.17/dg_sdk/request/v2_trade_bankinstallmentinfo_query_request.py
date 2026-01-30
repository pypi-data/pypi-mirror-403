from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_BANKINSTALLMENTINFO_QUERY



class V2TradeBankinstallmentinfoQueryRequest(object):
    """
    银行卡分期支持银行查询
    """

    # 页码
    page_num = ""
    # 每页条数
    page_size = ""
    # 产品号
    product_id = ""

    def post(self, extend_infos):
        """
        银行卡分期支持银行查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "page_num":self.page_num,
            "page_size":self.page_size,
            "product_id":self.product_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_BANKINSTALLMENTINFO_QUERY, required_params, need_verfy_sign=False)
