from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_QUICKBUCKLE_BIND_CARDINFO_QUERY



class V2QuickbuckleBindCardinfoQueryRequest(object):
    """
    一键绑卡-工行卡号查询
    """

    # 请求流水号
    req_seq_id = ""
    # 请求时间
    req_date = ""
    # 汇付Id
    huifu_id = ""
    # 产品Id
    product_id = ""
    # 银行卡开户姓名
    card_name = ""
    # 身份证类型
    cert_type = ""
    # 银行卡绑定身份证
    cert_no = ""
    # 银行卡绑定手机号
    card_mobile = ""
    # 回调地址
    notify_url = ""

    def post(self, extend_infos):
        """
        一键绑卡-工行卡号查询

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "product_id":self.product_id,
            "card_name":self.card_name,
            "cert_type":self.cert_type,
            "cert_no":self.cert_no,
            "card_mobile":self.card_mobile,
            "notify_url":self.notify_url
        }
        required_params.update(extend_infos)
        return request_post(V2_QUICKBUCKLE_BIND_CARDINFO_QUERY, required_params)
