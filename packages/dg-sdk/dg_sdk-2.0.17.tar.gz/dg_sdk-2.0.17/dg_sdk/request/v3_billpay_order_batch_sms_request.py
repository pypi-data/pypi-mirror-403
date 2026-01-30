from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V3_BILLPAY_ORDER_BATCH_SMS



class V3BillpayOrderBatchSmsRequest(object):
    """
    账单数据短信通知
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 账单编号
    bill_no = ""

    def post(self, extend_infos):
        """
        账单数据短信通知

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bill_no":self.bill_no
        }
        required_params.update(extend_infos)
        return request_post(V3_BILLPAY_ORDER_BATCH_SMS, required_params)
