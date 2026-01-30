from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_BILL_ENT_CREATE



class V2BillEntCreateRequest(object):
    """
    创建企业账单
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 付款人
    payer_id = ""
    # 账单名称
    bill_name = ""
    # 账单金额
    bill_amt = ""
    # 可支持的付款方式
    support_pay_type = ""
    # 账单截止日期
    bill_end_date = ""
    # 收款人信息
    payee_info = ""

    def post(self, extend_infos):
        """
        创建企业账单

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "payer_id":self.payer_id,
            "bill_name":self.bill_name,
            "bill_amt":self.bill_amt,
            "support_pay_type":self.support_pay_type,
            "bill_end_date":self.bill_end_date,
            "payee_info":self.payee_info
        }
        required_params.update(extend_infos)
        return request_post(V2_BILL_ENT_CREATE, required_params)
