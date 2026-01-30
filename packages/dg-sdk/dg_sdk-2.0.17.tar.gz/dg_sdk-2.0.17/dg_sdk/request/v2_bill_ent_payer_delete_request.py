from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_BILL_ENT_PAYER_DELETE



class V2BillEntPayerDeleteRequest(object):
    """
    删除付款人
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 付款人
    payer_id = ""

    def post(self, extend_infos):
        """
        删除付款人

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "payer_id":self.payer_id
        }
        required_params.update(extend_infos)
        return request_post(V2_BILL_ENT_PAYER_DELETE, required_params)
