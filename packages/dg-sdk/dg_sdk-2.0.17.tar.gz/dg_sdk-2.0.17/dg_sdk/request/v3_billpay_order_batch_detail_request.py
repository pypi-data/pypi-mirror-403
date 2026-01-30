from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V3_BILLPAY_ORDER_BATCH_DETAIL



class V3BillpayOrderBatchDetailRequest(object):
    """
    查询批量账单数据
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 账单编号与原创建批量账单数据请求流水号二选一必填，&lt;font color&#x3D;&quot;green&quot;&gt;示例值：BN2025091279190693&lt;/font&gt;;
    bill_no = ""
    # 原创建批量账单数据请求流水号原创建批量账单数据请求流水号，同一商户号当天唯一；与帐单编号二选一必填
    ori_req_seq_id = ""
    # 原创建批量账单数据请求日期原创建批量账单数据日期格式：yyyyMMdd，以北京时间为准；与帐单编号二选一必填
    ori_req_date = ""

    def post(self, extend_infos):
        """
        查询批量账单数据

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "bill_no":self.bill_no,
            "ori_req_seq_id":self.ori_req_seq_id,
            "ori_req_date":self.ori_req_date
        }
        required_params.update(extend_infos)
        return request_post(V3_BILLPAY_ORDER_BATCH_DETAIL, required_params)
