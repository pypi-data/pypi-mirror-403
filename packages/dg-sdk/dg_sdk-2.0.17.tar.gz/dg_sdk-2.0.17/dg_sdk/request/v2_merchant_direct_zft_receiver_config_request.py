from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_DIRECT_ZFT_RECEIVER_CONFIG



class V2MerchantDirectZftReceiverConfigRequest(object):
    """
    直付通分账关系绑定解绑
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付ID
    huifu_id = ""
    # 开发者的应用ID
    app_id = ""
    # 分账开关
    split_flag = ""
    # 分账接收方列表
    zft_split_receiver_list = ""
    # 状态
    status = ""

    def post(self, extend_infos):
        """
        直付通分账关系绑定解绑

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "app_id":self.app_id,
            "split_flag":self.split_flag,
            "zft_split_receiver_list":self.zft_split_receiver_list,
            "status":self.status
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_DIRECT_ZFT_RECEIVER_CONFIG, required_params)
