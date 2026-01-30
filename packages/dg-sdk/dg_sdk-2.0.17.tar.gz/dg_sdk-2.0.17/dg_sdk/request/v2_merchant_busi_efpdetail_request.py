from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_EFPDETAIL



class V2MerchantBusiEfpdetailRequest(object):
    """
    全渠道资金管理配置查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付id
    huifu_id = ""
    # 银行类型
    out_funds_gate_id = ""

    def post(self, extend_infos):
        """
        全渠道资金管理配置查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "out_funds_gate_id":self.out_funds_gate_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_EFPDETAIL, required_params)
