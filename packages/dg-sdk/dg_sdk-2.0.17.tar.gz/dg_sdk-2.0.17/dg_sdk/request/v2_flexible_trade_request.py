from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_FLEXIBLE_TRADE



class V2FlexibleTradeRequest(object):
    """
    灵工支付
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 出款方商户号
    out_huifu_id = ""
    # 交易阶段操作类型
    stage_operation_type = ""
    # 前段交易流水号** 当交易阶段操作类型为02时，该字段必填。填写的是交易阶段操作类型为01时交易已完成的交易全局流水号。 &lt;font color&#x3D;&quot;green&quot;&gt;示例值：20250620112533115566896&lt;/font&gt;
    phase_hf_seq_id = ""
    # 支付金额
    ord_amt = ""
    # 分账对象
    acct_split_bunch = ""

    def post(self, extend_infos):
        """
        灵工支付

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "out_huifu_id":self.out_huifu_id,
            "stage_operation_type":self.stage_operation_type,
            "phase_hf_seq_id":self.phase_hf_seq_id,
            "ord_amt":self.ord_amt,
            "acct_split_bunch":self.acct_split_bunch
        }
        required_params.update(extend_infos)
        return request_post(V2_FLEXIBLE_TRADE, required_params)
