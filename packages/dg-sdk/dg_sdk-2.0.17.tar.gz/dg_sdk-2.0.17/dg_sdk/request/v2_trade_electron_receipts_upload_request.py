from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ELECTRON_RECEIPTS_UPLOAD



class V2TradeElectronReceiptsUploadRequest(object):
    """
    上传电子小票图片
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 商户汇付Id
    huifu_id = ""
    # 原请求日期
    org_req_date = ""
    # 原请求流水号原请求流水号、原交易返回的全局流水号至少要送其中一项；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：2021091708126665001&lt;/font&gt;
    org_req_seq_id = ""
    # 汇付全局流水号原请求流水号、原交易返回的全局流水号至少要送其中一项；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：00290TOP1GR210919004230P853ac13262200000&lt;/font&gt;
    org_hf_seq_id = ""
    # 票据信息
    receipt_data = ""
    # 文件名称
    file_name = ""
    # 图片内容
    image_content = ""

    def post(self, extend_infos):
        """
        上传电子小票图片

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "org_req_date":self.org_req_date,
            "org_req_seq_id":self.org_req_seq_id,
            "org_hf_seq_id":self.org_hf_seq_id,
            "receipt_data":self.receipt_data,
            "file_name":self.file_name,
            "image_content":self.image_content
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ELECTRON_RECEIPTS_UPLOAD, required_params)
