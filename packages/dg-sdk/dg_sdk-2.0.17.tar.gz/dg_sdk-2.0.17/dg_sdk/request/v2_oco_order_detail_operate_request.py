from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_OCO_ORDER_DETAIL_OPERATE



class V2OcoOrderDetailOperateRequest(object):
    """
    全渠道订单分账明细操作
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户号
    huifu_id = ""
    # 分账数据源
    busi_source = ""
    # 业务订单号
    oco_order_id = ""
    # 操作类型
    operate_type = ""
    # 支付方式枚举：BALANCE-余额支付 EFP-全域资金付款；备注：当operate_type&#x3D;SPLIT 立即分账时，pay_type必填，且若为退款，按原交易类型原路返回；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：BALANCE&lt;/font&gt;
    pay_type = ""

    def post(self, extend_infos):
        """
        全渠道订单分账明细操作

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "busi_source":self.busi_source,
            "oco_order_id":self.oco_order_id,
            "operate_type":self.operate_type,
            "pay_type":self.pay_type
        }
        required_params.update(extend_infos)
        return request_post(V2_OCO_ORDER_DETAIL_OPERATE, required_params)
