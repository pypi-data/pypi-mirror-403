from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_SETTLE_COLLECTION_RULE_ADD



class V2TradeSettleCollectionRuleAddRequest(object):
    """
    新增归集配置
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 转入方商户号
    in_huifu_id = ""
    # 转出方商户号
    out_huifu_id = ""
    # 签约人手机号协议类型为电子协议时必填，必须为法人手机号。&lt;font color&#x3D;&quot;green&quot;&gt;示例值：13911111111&lt;/font&gt;
    sign_user_mobile_no = ""
    # 协议文件Id协议类型为纸质协议时必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e529&lt;/font&gt;
    file_id = ""

    def post(self, extend_infos):
        """
        新增归集配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "in_huifu_id":self.in_huifu_id,
            "out_huifu_id":self.out_huifu_id,
            "sign_user_mobile_no":self.sign_user_mobile_no,
            "file_id":self.file_id
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_SETTLE_COLLECTION_RULE_ADD, required_params)
