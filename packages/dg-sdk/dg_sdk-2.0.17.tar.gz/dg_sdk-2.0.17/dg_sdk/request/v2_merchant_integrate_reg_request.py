from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_INTEGRATE_REG



class V2MerchantIntegrateRegRequest(object):
    """
    商户统一进件接口(2022)
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 渠道商汇付id
    upper_huifu_id = ""
    # 公司类型
    ent_type = ""
    # 商户名称
    reg_name = ""
    # 经营类型
    busi_type = ""
    # 经营详细地址
    detail_addr = ""
    # 经营省
    prov_id = ""
    # 经营市
    area_id = ""
    # 经营区
    district_id = ""
    # 联系人信息
    contact_info = ""
    # 卡信息配置实体
    card_info = ""
    # 取现配置列表jsonArray格式 ；
    cash_config = ""
    # 结算配置jsonObject格式；
    settle_config = ""

    def post(self, extend_infos):
        """
        商户统一进件接口(2022)

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "upper_huifu_id":self.upper_huifu_id,
            "ent_type":self.ent_type,
            "reg_name":self.reg_name,
            "busi_type":self.busi_type,
            "detail_addr":self.detail_addr,
            "prov_id":self.prov_id,
            "area_id":self.area_id,
            "district_id":self.district_id,
            "contact_info":self.contact_info,
            "card_info":self.card_info,
            "cash_config":self.cash_config,
            "settle_config":self.settle_config
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_INTEGRATE_REG, required_params)
