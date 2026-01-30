from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_EFP_SURROGATE



class V2EfpSurrogateRequest(object):
    """
    全渠道资金付款申请
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付id
    huifu_id = ""
    # 交易金额.单位:元，2位小数
    cash_amt = ""
    # 银行账号使用斗拱系统的公钥对银行账号进行RSA加密得到秘文；  示例值：b9LE5RccVVLChrHgo9lvp……PhWhjKrWg2NPfbe0mkQ&#x3D;&#x3D; 到账类型标识为E或P时必填
    card_no = ""
    # 银行编号银行编号 到账类型标识为E或P时必填
    bank_code = ""
    # 银行卡用户名银行卡用户名 到账类型标识为E或P时必填
    card_name = ""
    # 到账类型标识
    card_acct_type = ""
    # 省份到账类型标识为E或P时必填
    prov_id = ""
    # 地区到账类型标识为E或P时必填
    area_id = ""
    # 手机号对私必填，使用斗拱系统的公钥对手机号进行RSA加密得到秘文；  示例值：b9LE5RccVVLChrHgo9lvp……PhWhjKrWg2NPfbe0mkUDd
    mobile_no = ""
    # 证件类型证件类型01：身份证  03：护照  06：港澳通行证  07：台湾通行证  09：外国人居留证  11：营业执照  12：组织机构代码证  14：统一社会信用代码  99：其他  示例值：14 到账类型标识为E或P时必填
    cert_type = ""
    # 证件号使用斗拱系统的公钥对证件号进行RSA加密得到秘文；  示例值：b9LE5RccVVLChrHgo9lvp……PhWhjKrWg2NPfbe0mkQ 到账类型标识为P时必填
    cert_no = ""
    # 统一社会信用代码到账类型标识为E时必填
    licence_code = ""
    # 入账接收方对象json格式,到账类型标识为H时必填
    acct_split_bunch = ""

    def post(self, extend_infos):
        """
        全渠道资金付款申请

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "cash_amt":self.cash_amt,
            "card_no":self.card_no,
            "bank_code":self.bank_code,
            "card_name":self.card_name,
            "card_acct_type":self.card_acct_type,
            "prov_id":self.prov_id,
            "area_id":self.area_id,
            "mobile_no":self.mobile_no,
            "cert_type":self.cert_type,
            "cert_no":self.cert_no,
            "licence_code":self.licence_code,
            "acct_split_bunch":self.acct_split_bunch
        }
        required_params.update(extend_infos)
        return request_post(V2_EFP_SURROGATE, required_params)
