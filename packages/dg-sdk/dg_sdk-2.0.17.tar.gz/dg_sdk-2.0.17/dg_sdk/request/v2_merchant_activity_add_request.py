from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_ACTIVITY_ADD



class V2MerchantActivityAddRequest(object):
    """
    商户活动报名
    """

    # 请求日期
    req_date = ""
    # 请求流水号
    req_seq_id = ""
    # 汇付客户Id
    huifu_id = ""
    # 营业执照图片调用[图片上传接口](http://paas.huifu.com/open/doc/api/#/shgl/shjj/api_shjj_shtpsc)获取jfile文件id；[示例图片](https://cloudpnrcdn.oss-cn-shanghai.aliyuncs.com/spin/imgs/%E8%90%A5%E4%B8%9A%E6%89%A7%E7%85%A7%E7%A4%BA%E4%BE%8B.png)参考&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e529&lt;/font&gt;&lt;br/&gt;活动类型为支付宝谷雨活动时无需填写任何资料
    bl_photo = ""
    # 店内环境图片参加教育食堂、非校园餐饮、非盈利、停车缴费行业时必传；调用[图片上传接口](http://paas.huifu.com/open/doc/api/#/shgl/shjj/api_shjj_shtpsc)获取jfile文件id；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e529&lt;/font&gt;&lt;br/&gt;活动类型为支付宝谷雨活动时无需填写任何资料
    dh_photo = ""
    # 手续费类型
    fee_type = ""
    # 整体门面图片（门头照）参加教育食堂行业、非校园餐饮、非盈利、线下教培、公办医院、商业医疗时必传；调用[图片上传接口](http://paas.huifu.com/open/doc/api/#/shgl/shjj/api_shjj_shtpsc)获取jfile文件id；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e529&lt;/font&gt;&lt;br/&gt;活动类型为支付宝谷雨活动时无需填写任何资料&lt;br/&gt;若为线下教培活动,[示例图片](https://cloudpnrcdn.oss-cn-shanghai.aliyuncs.com/spin/imgs/%E9%97%A8%E5%A4%B4%E7%85%A7%E7%A4%BA%E4%BE%8B.png)参考
    mm_photo = ""
    # 收银台照片参加教育食堂行业、线下教培、公办医院时必传；调用[图片上传接口](http://paas.huifu.com/open/doc/api/#/shgl/shjj/api_shjj_shtpsc)获取jfile文件id；&lt;br/&gt;&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e529&lt;/font&gt;&lt;br/&gt;活动类型为支付宝谷雨活动时无需填写任何资料
    syt_photo = ""
    # 支付通道
    pay_way = ""

    def post(self, extend_infos):
        """
        商户活动报名

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_date":self.req_date,
            "req_seq_id":self.req_seq_id,
            "huifu_id":self.huifu_id,
            "bl_photo":self.bl_photo,
            "dh_photo":self.dh_photo,
            "fee_type":self.fee_type,
            "mm_photo":self.mm_photo,
            "syt_photo":self.syt_photo,
            "pay_way":self.pay_way
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_ACTIVITY_ADD, required_params)
