from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_BILL_ENT_CHANGESTAT



class V2BillEntChangestatRequest(object):
    """
    企业账单状态变更
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 账单编号
    bill_no = ""
    # 变更状态
    bill_stat = ""

    def post(self, extend_infos):
        """
        企业账单状态变更

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bill_no":self.bill_no,
            "bill_stat":self.bill_stat
        }
        required_params.update(extend_infos)
        return request_post(V2_BILL_ENT_CHANGESTAT, required_params)
