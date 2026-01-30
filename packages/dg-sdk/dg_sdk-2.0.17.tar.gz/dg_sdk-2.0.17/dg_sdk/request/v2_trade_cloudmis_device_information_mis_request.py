from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_TRADE_CLOUDMIS_DEVICE_INFORMATION_MIS



class V2TradeCloudmisDeviceInformationMisRequest(object):
    """
    终端云MIS交易
    """

    # 请求流水号
    req_id = ""
    # 终端设备号
    device_id = ""
    # 商户号
    huifu_id = ""
    # 交易信息
    json_data = ""

    def post(self, extend_infos):
        """
        终端云MIS交易

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_id":self.req_id,
            "device_id":self.device_id,
            "huifu_id":self.huifu_id,
            "json_data":self.json_data
        }
        required_params.update(extend_infos)
        return request_post(V2_TRADE_CLOUDMIS_DEVICE_INFORMATION_MIS, required_params)
