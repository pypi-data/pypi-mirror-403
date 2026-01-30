from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_QUICKBUCKLE_WITHHOLD_QUERY



class V2QuickbuckleWithholdQueryRequest(object):
    """
    代扣绑卡查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付Id
    huifu_id = ""
    # 客户系统用户id 
    out_cust_id = ""
    # 绑卡订单号
    order_id = ""
    # 绑卡订单日期
    order_date = ""

    def post(self, extend_infos):
        """
        代扣绑卡查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "out_cust_id":self.out_cust_id,
            "order_id":self.order_id,
            "order_date":self.order_date
        }
        required_params.update(extend_infos)
        return request_post(V2_QUICKBUCKLE_WITHHOLD_QUERY, required_params)
