from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_INVOICE_OPEN



class V2InvoiceOpenRequest(object):
    """
    发票开具
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付商户号huifu_id与ext_mer_id二选一必填，汇付商户号优先；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：6666000109812123&lt;/font&gt;
    huifu_id = ""
    # 外部商户号&lt;font color&#x3D;&quot;green&quot;&gt;示例值：&lt;/font&gt;
    ext_mer_id = ""
    # 渠道号汇付商户号为空时，必传；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：6666000109812124&lt;/font&gt;
    channel_id = ""
    # 发票类型
    ivc_type = ""
    # 开票类型
    open_type = ""
    # 购方单位名称
    buyer_name = ""
    # 含税合计金额(元)
    order_amt = ""
    # 冲红原因open_type&#x3D;1时必填01：开票有误02：销货退回03：服务终止04：销售转让
    red_apply_reason = ""
    # 冲红申请来源open_type&#x3D;1时必填01：销方02：购方
    red_apply_source = ""
    # 原发票代码openType&#x3D;1时必填；参见[发票右上角](https://paas.huifu.com/open/doc/api/#/fp/api_fp_yanglitu.md)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：144032209110&lt;/font&gt;
    ori_ivc_code = ""
    # 原发票号码openType&#x3D;1时必填；参见[发票右上角](https://paas.huifu.com/open/doc/api/#/fp/api_fp_yanglitu.md)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：20685767&lt;/font&gt;
    ori_ivc_number = ""
    # 开票商品信息
    goods_infos = ""
    # 不动产销售特殊字段specialFlag为05时，必填；jsonArray格式
    estate_sales = ""
    # 不动产租赁特殊字段specialFlag为16时，必填；jsonArray格式
    estate_lease = ""

    def post(self, extend_infos):
        """
        发票开具

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "ext_mer_id":self.ext_mer_id,
            "channel_id":self.channel_id,
            "ivc_type":self.ivc_type,
            "open_type":self.open_type,
            "buyer_name":self.buyer_name,
            "order_amt":self.order_amt,
            "red_apply_reason":self.red_apply_reason,
            "red_apply_source":self.red_apply_source,
            "ori_ivc_code":self.ori_ivc_code,
            "ori_ivc_number":self.ori_ivc_number,
            "goods_infos":self.goods_infos,
            "estate_sales":self.estate_sales,
            "estate_lease":self.estate_lease
        }
        required_params.update(extend_infos)
        return request_post(V2_INVOICE_OPEN, required_params)
