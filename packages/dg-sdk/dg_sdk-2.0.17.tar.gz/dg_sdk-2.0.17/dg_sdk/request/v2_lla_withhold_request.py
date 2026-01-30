from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LLA_WITHHOLD



class V2LlaWithholdRequest(object):
    """
    代运营佣金代扣
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 代运营汇付id
    agency_huifu_id = ""
    # 商家汇付id
    merchant_huifu_id = ""
    # 平台
    platform_type = ""
    # 提现id
    encash_seq_id = ""
    # 绑卡id
    token_no = ""
    # 抽佣金额
    trans_amt = ""
    # 银行扩展数据
    extend_pay_data = ""
    # 设备信息
    terminal_device_data = ""
    # 安全信息
    risk_check_data = ""

    def post(self, extend_infos):
        """
        代运营佣金代扣

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "agency_huifu_id":self.agency_huifu_id,
            "merchant_huifu_id":self.merchant_huifu_id,
            "platform_type":self.platform_type,
            "encash_seq_id":self.encash_seq_id,
            "token_no":self.token_no,
            "trans_amt":self.trans_amt,
            "extend_pay_data":self.extend_pay_data,
            "terminal_device_data":self.terminal_device_data,
            "risk_check_data":self.risk_check_data
        }
        required_params.update(extend_infos)
        return request_post(V2_LLA_WITHHOLD, required_params)
