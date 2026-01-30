from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_CERTINFO_ADD



class V2MerchantDirectCertinfoAddRequest(object):
    """
    证书登记
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 渠道商汇付Id
    upper_huifu_id = ""
    # 开通类型
    pay_way = ""
    # 开发者的应用ID
    app_id = ""
    # 文件列表
    file_list = ""

    def post(self, extend_infos):
        """
        证书登记

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "upper_huifu_id":self.upper_huifu_id,
            "pay_way":self.pay_way,
            "app_id":self.app_id,
            "file_list":self.file_list
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_CERTINFO_ADD, required_params)
