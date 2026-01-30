from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_BILL_CONFIG



class V2MerchantBusiBillConfigRequest(object):
    """
    交易结算对账文件配置
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 汇付机构编号
    huifu_id = ""
    # 对账文件生成开关
    recon_send_flag = ""
    # 对账单类型
    file_type = ""

    def post(self, extend_infos):
        """
        交易结算对账文件配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "recon_send_flag":self.recon_send_flag,
            "file_type":self.file_type
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_BILL_CONFIG, required_params)
