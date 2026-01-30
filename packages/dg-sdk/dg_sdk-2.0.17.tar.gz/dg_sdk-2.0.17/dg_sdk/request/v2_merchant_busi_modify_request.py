from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_MODIFY



class V2MerchantBusiModifyRequest(object):
    """
    商户业务开通修改
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付客户Id
    huifu_id = ""
    # *线上业务类型编码*开通快捷、网银、余额支付Pro版、分账必填；参见[线上业务类型编码及补充材料说明](https://cloudpnrcdn.oss-cn-shanghai.aliyuncs.com/opps/api/prod/download_file/kyc/KYC-%E7%BA%BF%E4%B8%8A%E4%B8%9A%E5%8A%A1%E7%B1%BB%E5%9E%8B%E7%BC%96%E7%A0%81%E5%8F%8A%E8%A1%A5%E5%85%85%E6%9D%90%E6%96%99%E8%AF%B4%E6%98%8E.xlsx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：H7999AL&lt;/font&gt;
    online_busi_type = ""
    # 签约人jsonObject格式；agreement_info中选择电子签约时必填；个人商户填本人信息。
    sign_user_info = ""

    def post(self, extend_infos):
        """
        商户业务开通修改

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "online_busi_type":self.online_busi_type,
            "sign_user_info":self.sign_user_info
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_MODIFY, required_params)
