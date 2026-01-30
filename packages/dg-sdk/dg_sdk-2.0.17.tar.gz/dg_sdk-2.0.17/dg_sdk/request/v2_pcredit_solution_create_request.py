from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_PCREDIT_SOLUTION_CREATE



class V2PcreditSolutionCreateRequest(object):
    """
    创建花呗分期方案
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 汇付客户Id
    huifu_id = ""
    # 花呗分期商家贴息活动名称
    activity_name = ""
    # 活动开始时间
    start_time = ""
    # 活动结束时间
    end_time = ""
    # 免息金额下限(元)
    min_money_limit = ""
    # 免息金额上限(元)
    max_money_limit = ""
    # 花呗分期贴息预算金额
    amount_budget = ""
    # 花呗分期数集合
    install_num_str_list = ""
    # 预算提醒金额(元)
    budget_warning_money = ""
    # 预算提醒邮件列表
    budget_warning_mail_list = ""
    # 预算提醒手机号列表
    budget_warning_mobile_no_list = ""
    # 子门店信息集合
    sub_shop_info_list = ""

    def post(self, extend_infos):
        """
        创建花呗分期方案

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "activity_name":self.activity_name,
            "start_time":self.start_time,
            "end_time":self.end_time,
            "min_money_limit":self.min_money_limit,
            "max_money_limit":self.max_money_limit,
            "amount_budget":self.amount_budget,
            "install_num_str_list":self.install_num_str_list,
            "budget_warning_money":self.budget_warning_money,
            "budget_warning_mail_list":self.budget_warning_mail_list,
            "budget_warning_mobile_no_list":self.budget_warning_mobile_no_list,
            "sub_shop_info_list":self.sub_shop_info_list
        }
        required_params.update(extend_infos)
        return request_post(V2_PCREDIT_SOLUTION_CREATE, required_params)
