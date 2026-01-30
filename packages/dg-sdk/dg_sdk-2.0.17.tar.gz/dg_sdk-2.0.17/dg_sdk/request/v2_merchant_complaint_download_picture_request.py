from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_COMPLAINT_DOWNLOAD_PICTURE



class V2MerchantComplaintDownloadPictureRequest(object):
    """
    投诉图片下载
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 下载图片的url
    media_url = ""
    # 投诉单号
    complaint_id = ""

    def post(self, extend_infos):
        """
        投诉图片下载

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "media_url":self.media_url,
            "complaint_id":self.complaint_id
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_COMPLAINT_DOWNLOAD_PICTURE, required_params)
