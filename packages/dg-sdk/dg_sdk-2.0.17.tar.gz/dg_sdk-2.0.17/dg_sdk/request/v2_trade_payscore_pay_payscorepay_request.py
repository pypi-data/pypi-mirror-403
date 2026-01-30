from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_PAYSCORE_PAY_PAYSCOREPAY



class V2TradePayscorePayPayscorepayRequest(object):
    """
    支付分扣款
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 商户号
    huifu_id = ""
    # 扣款登记创建请求流水号deduct_req_seq_id与deduct_hf_seq_id二选一；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2022012614120615001&lt;/font&gt;
    deduct_req_seq_id = ""
    # 扣款登记返回的汇付全局流水号deduct_req_seq_id与deduct_hf_seq_id二选一；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：00470topo1A211015160805P090ac132fef00000&lt;/font&gt;
    deduct_hf_seq_id = ""
    # 微信扣款单号
    out_trade_no = ""
    # 商品描述
    goods_desc = ""
    # 安全信息
    risk_check_data = ""

    def post(self, extend_infos):
        """
        支付分扣款

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "deduct_req_seq_id":self.deduct_req_seq_id,
            "deduct_hf_seq_id":self.deduct_hf_seq_id,
            "out_trade_no":self.out_trade_no,
            "goods_desc":self.goods_desc,
            "risk_check_data":self.risk_check_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_PAYSCORE_PAY_PAYSCOREPAY, required_params)
