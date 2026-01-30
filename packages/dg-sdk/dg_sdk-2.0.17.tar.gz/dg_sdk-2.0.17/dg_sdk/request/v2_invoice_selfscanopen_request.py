from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_INVOICE_SELFSCANOPEN



class V2InvoiceSelfscanopenRequest(object):
    """
    自助扫码开票
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 发票类型
    ivc_type = ""
    # 开票类型
    open_type = ""
    # 含税合计金额（元）
    order_amt = ""
    # 开票商品信息
    goods_infos = ""

    def post(self, extend_infos):
        """
        自助扫码开票

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "ivc_type":self.ivc_type,
            "open_type":self.open_type,
            "order_amt":self.order_amt,
            "goods_infos":self.goods_infos
        }
        required_params.update(extend_infos)
        return request_post(V2_INVOICE_SELFSCANOPEN, required_params)
