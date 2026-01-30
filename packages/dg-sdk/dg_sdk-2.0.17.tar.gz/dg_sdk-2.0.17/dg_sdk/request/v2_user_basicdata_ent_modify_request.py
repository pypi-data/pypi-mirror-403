from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_USER_BASICDATA_ENT_MODIFY



class V2UserBasicdataEntModifyRequest(object):
    """
    企业用户基本信息修改
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 汇付客户Id
    huifu_id = ""
    # 法人国籍法人的证件类型为外国人居留证时，必填，参见《[国籍编码](https://cloudpnrcdn.oss-cn-shanghai.aliyuncs.com/opps/api/prod/download_file/area/%E5%9B%BD%E7%B1%8D.xlsx)》&lt;font color&#x3D;&quot;green&quot;&gt;示例值：CHN&lt;/font&gt;
    legal_cert_nationality = ""

    def post(self, extend_infos):
        """
        企业用户基本信息修改

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "legal_cert_nationality":self.legal_cert_nationality
        }
        required_params.update(extend_infos)
        return request_post(V2_USER_BASICDATA_ENT_MODIFY, required_params)
