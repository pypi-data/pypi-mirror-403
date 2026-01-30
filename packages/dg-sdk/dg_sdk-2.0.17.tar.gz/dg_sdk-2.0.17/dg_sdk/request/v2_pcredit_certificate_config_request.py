from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_PCREDIT_CERTIFICATE_CONFIG



class V2PcreditCertificateConfigRequest(object):
    """
    分期证书配置
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 开发者的应用ID
    app_id = ""
    # 证书文件列表
    file_list = ""

    def post(self, extend_infos):
        """
        分期证书配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "app_id":self.app_id,
            "file_list":self.file_list
        }
        required_params.update(extend_infos)
        return request_post(V2_PCREDIT_CERTIFICATE_CONFIG, required_params)
