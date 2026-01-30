from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_USER_BASICDATA_INDV



class V2UserBasicdataIndvRequest(object):
    """
    个人用户基本信息开户
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 个人姓名
    name = ""
    # 个人证件类型
    cert_type = ""
    # 个人证件号码
    cert_no = ""
    # 个人证件有效期类型
    cert_validity_type = ""
    # 个人证件有效期开始日期
    cert_begin_date = ""
    # 个人国籍个人证件类型为外国人居留证时，必填，参见《[国籍编码](https://cloudpnrcdn.oss-cn-shanghai.aliyuncs.com/opps/api/prod/download_file/area/%E5%9B%BD%E7%B1%8D.xlsx)》&lt;font color&#x3D;&quot;green&quot;&gt;示例值：CHN&lt;/font&gt;
    cert_nationality = ""
    # 手机号
    mobile_no = ""
    # 地址开通中信E管家必填
    address = ""

    def post(self, extend_infos):
        """
        个人用户基本信息开户

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "name":self.name,
            "cert_type":self.cert_type,
            "cert_no":self.cert_no,
            "cert_validity_type":self.cert_validity_type,
            "cert_begin_date":self.cert_begin_date,
            "cert_nationality":self.cert_nationality,
            "mobile_no":self.mobile_no,
            "address":self.address
        }
        required_params.update(extend_infos)
        return request_post(V2_USER_BASICDATA_INDV, required_params)
