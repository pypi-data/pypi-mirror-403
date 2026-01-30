from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_SETTLEMENT_SURROGATE



class V2TradeSettlementSurrogateRequest(object):
    """
    银行卡代发
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户号
    huifu_id = ""
    # 代发金额
    cash_amt = ""
    # 代发用途描述
    purpose_desc = ""
    # 省份选填，参见[代发省市地区码](https://cloudpnrcdn.oss-cn-shanghai.aliyuncs.com/opps/api/prod/download_file/area/%E6%96%97%E6%8B%B1%E4%BB%A3%E5%8F%91%E7%9C%81%E4%BB%BD%E5%9C%B0%E5%8C%BA%E7%BC%96%E7%A0%81.xlsx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：0013&lt;/font&gt;&lt;br/&gt;对公代发(省份+地区)与联行号信息二选一填入；对私代发非必填；
    province = ""
    # 地区选填，参见[代发省市地区码](https://cloudpnrcdn.oss-cn-shanghai.aliyuncs.com/opps/api/prod/download_file/area/%E6%96%97%E6%8B%B1%E4%BB%A3%E5%8F%91%E7%9C%81%E4%BB%BD%E5%9C%B0%E5%8C%BA%E7%BC%96%E7%A0%81.xlsx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：1301&lt;/font&gt;&lt;br/&gt;对公代发(省份+地区)与联行号信息二选一填入；对私代发非必填；
    area = ""
    # 银行编号参考： [银行编码](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_yhbm)； &lt;font color&#x3D;&quot;green&quot;&gt;&lt;br/&gt; 选填 ，card_acct_type&#x3D;E 时必填， 示例值：01040000&lt;/font&gt;
    bank_code = ""
    # 联行号选填，参见：[银行支行编码](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_yhzhbm) &lt;font color&#x3D;&quot;green&quot;&gt;示例值：102290026507&lt;/font&gt;&lt;br/&gt;对公代发(省份+地区)与联行号信息二选一填入；对私代发非必填；
    correspondent_code = ""
    # 银行卡用户名
    bank_account_name = ""
    # 对公对私标识
    card_acct_type = ""
    # 银行账号密文
    bank_card_no_crypt = ""
    # 证件号密文
    certificate_no_crypt = ""
    # 证件类型对私必填，类型&lt;br/&gt;01：身份证&lt;br/&gt;03：护照（国内）&lt;br/&gt;09：外国人居留证&lt;br/&gt;15：港澳台居住证&lt;br/&gt;16：回乡证&lt;br/&gt;17：台胞证&lt;br/&gt;
    certificate_type = ""
    # 到账日期类型
    into_acct_date_type = ""

    def post(self, extend_infos):
        """
        银行卡代发

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "cash_amt":self.cash_amt,
            "purpose_desc":self.purpose_desc,
            "province":self.province,
            "area":self.area,
            "bank_code":self.bank_code,
            "correspondent_code":self.correspondent_code,
            "bank_account_name":self.bank_account_name,
            "card_acct_type":self.card_acct_type,
            "bank_card_no_crypt":self.bank_card_no_crypt,
            "certificate_no_crypt":self.certificate_no_crypt,
            "certificate_type":self.certificate_type,
            "into_acct_date_type":self.into_acct_date_type
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_SETTLEMENT_SURROGATE, required_params)
