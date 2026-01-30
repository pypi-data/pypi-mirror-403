from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_ELECTRON_RECEIPTS_PICTURE_UPLOAD



class V2TradeElectronReceiptsPictureUploadRequest(object):
    """
    图片上传
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 三方通道类型
    third_channel_type = ""
    # 文件名称
    file_name = ""
    # 图片内容
    image_content = ""

    def post(self, extend_infos):
        """
        图片上传

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "third_channel_type":self.third_channel_type,
            "file_name":self.file_name,
            "image_content":self.image_content
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_ELECTRON_RECEIPTS_PICTURE_UPLOAD, required_params)
