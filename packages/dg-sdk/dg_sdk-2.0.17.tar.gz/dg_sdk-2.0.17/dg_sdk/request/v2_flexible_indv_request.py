from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_FLEXIBLE_INDV



class V2FlexibleIndvRequest(object):
    """
    灵工个人用户进件
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 渠道商/商户汇付Id
    upper_huifu_id = ""
    # 基本信息
    basic_info = ""
    # 卡信息
    card_info = ""

    def post(self, extend_infos):
        """
        灵工个人用户进件

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "upper_huifu_id":self.upper_huifu_id,
            "basic_info":self.basic_info,
            "card_info":self.card_info
        }
        required_params.update(extend_infos)
        return request_post(V2_FLEXIBLE_INDV, required_params)
