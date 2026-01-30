from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_LINKAPP_STORE_SHOPLIST



class V2LinkappStoreShoplistRequest(object):
    """
    三方门店查询（三方门店绑定一阶段）
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付商户号
    huifu_id = ""
    # 平台类型
    platform_type = ""

    def post(self, extend_infos):
        """
        三方门店查询（三方门店绑定一阶段）

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "platform_type":self.platform_type
        }
        required_params.update(extend_infos)
        return request_post(V2_LINKAPP_STORE_SHOPLIST, required_params)
