from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_SUPPLEMENTARY_PICTURE
import os


class V2SupplementaryPictureRequest(object):
    """
    图片上传
    """

    # 业务请求流水号
    req_seq_id = ""
    # 业务请求日期
    req_date = ""
    # 图片类型
    file_type = ""

    def post(self, extend_infos):
        """
        图片上传

        :param extend_infos: 扩展字段字典
        :return:
        """

        file = {'picture': (
            os.path.basename(self.picture), open(self.picture, 'rb'), 'application/octet-stream')}

        required_params = {
            "file_type": self.file_type,
            "picture": os.path.basename(self.picture)
        }
        return request_post(V2_SUPPLEMENTARY_PICTURE, required_params, file, need_sign=False, need_verfy_sign=False)
