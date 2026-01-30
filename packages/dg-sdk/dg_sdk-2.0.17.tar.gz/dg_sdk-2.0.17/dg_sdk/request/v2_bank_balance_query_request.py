from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_BANK_BALANCE_QUERY



class V2BankBalanceQueryRequest(object):
    """
    电子账户余额查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付Id
    huifu_id = ""

    def post(self, extend_infos):
        """
        电子账户余额查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id
        }
        required_params.update(extend_infos)
        return request_post(V2_BANK_BALANCE_QUERY, required_params)
