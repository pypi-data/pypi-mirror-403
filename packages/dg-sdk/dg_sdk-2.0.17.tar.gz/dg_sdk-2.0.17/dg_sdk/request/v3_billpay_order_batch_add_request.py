from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V3_BILLPAY_ORDER_BATCH_ADD



class V3BillpayOrderBatchAddRequest(object):
    """
    创建批量账单数据
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 账单项目编号
    project_no = ""
    # 用户资料信息列表
    user_doc_info_list = ""
    # 账单收费项信息列表
    payment_info_list = ""

    def post(self, extend_infos):
        """
        创建批量账单数据

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "project_no":self.project_no,
            "user_doc_info_list":self.user_doc_info_list,
            "payment_info_list":self.payment_info_list
        }
        required_params.update(extend_infos)
        return request_post(V3_BILLPAY_ORDER_BATCH_ADD, required_params)
