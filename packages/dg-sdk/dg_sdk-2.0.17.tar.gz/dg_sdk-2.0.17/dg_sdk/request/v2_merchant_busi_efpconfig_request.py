from dg_sdk.core.request_tools import request_post
from dg_sdk.request.request_api_urls import V2_MERCHANT_BUSI_EFPCONFIG



class V2MerchantBusiEfpconfigRequest(object):
    """
    全渠道资金管理配置
    """

    # 请求流水号
    req_seq_id = ""
    # 请求日期
    req_date = ""
    # 商户汇付id
    huifu_id = ""
    # 所属渠道商
    upper_huifu_id = ""
    # 支付手续费外扣汇付ID支付手续费外扣标记为1时必填；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：6666000109812123&lt;/font&gt;
    out_fee_huifuid = ""
    # 全域资金开户使用的银行卡信息首次开通时必填 jsonObject格式
    out_order_acct_card = ""
    # 全域资金开户手续费首次开通时必填 jsonObject格式
    out_order_acct_open_fees = ""
    # 业务模式acquiringMode:收单模式 switch_state为1时必填
    business_model = ""
    # 银行类型switch_state有值时需填写； ht1-华通银行，xw0-XW银行，ss0-苏商银行；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：ht1&lt;/font&gt;
    out_funds_gate_id = ""
    # 签约人信息switch_state为1时必填 jsonObject格式
    sign_user_info = ""
    # 入账来源开通全域资金时需填写；01:抖音 02:美团 03:快手 04:拼多多 05:小红书 06:淘宝/天猫/飞猪 07:微信视频号/微信小店 08:京东 09:饿了么 11:得物 12:唯品会 13:携程 14:支付宝直连 15:微信直连 16:滴滴加油 17:团油 18:通联 19:易宝 20:百度 21:顺丰22:希音23:高德 多个逗号分隔；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：01,02,05&lt;/font&gt;；
    acct_source = ""
    # 抖音合作证明材料入账来源包含01:抖音时必填 文件类型F535；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    dy_cooperation_prove_pic = ""
    # 美团合作证明材料入账来源包含02:美团时必填 文件类型F536；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    mt_cooperation_prove_pic = ""
    # 快手合作证明材料入账来源包含03:快手时必填 文件类型F537；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    ks_cooperation_prove_pic = ""
    # 拼多多合作证明材料入账来源包含04:拼多多时必填 文件类型F538；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    pdd_cooperation_prove_pic = ""
    # 小红书合作证明材料入账来源包含05:小红书时必填 文件类型F539；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    xhs_cooperation_prove_pic = ""
    # 淘宝天猫飞猪合作证明材料入账来源包含06:淘宝天猫飞猪时必填 文件类型F540；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    zfb_cooperation_prove_pic = ""
    # 微信视频号合作证明材料入账来源包含07:微信视频号时必填 文件类型F541；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    wx_cooperation_prove_pic = ""
    # 京东合作证明材料入账来源包含08:京东时必填 文件类型F542；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    jd_cooperation_prove_pic = ""
    # 饿了么合作证明材料入账来源包含09:饿了么时必填 文件类型F543；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    elm_cooperation_prove_pic = ""
    # 得物合作证明材料入账来源包含11:得物时必填 文件类型F591；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    dw_cooperation_prove_pic = ""
    # 唯品会合作证明材料入账来源包含12:唯品会时必填 文件类型F592；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    wph_cooperation_prove_pic = ""
    # 携程合作证明材料入账来源包含13:携程时必填 文件类型F593；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    xc_cooperation_prove_pic = ""
    # 支付宝直连合作证明材料入账来源包含14:支付宝直连时必填 文件类型F594；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    zfbzl_cooperation_prove_pic = ""
    # 微信直连合作证明材料入账来源包含15:微信直连时必填 文件类型F595；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    wxzl_cooperation_prove_pic = ""
    # 滴滴加油合作证明材料入账来源包含16:滴滴加油时必填 文件类型F596；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    ddjy_cooperation_prove_pic = ""
    # 团油合作证明材料入账来源包含17:团油时必填 文件类型F597；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    ty_cooperation_prove_pic = ""
    # 通联合作证明材料入账来源包含18:通联时必填 文件类型F598；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    tl_cooperation_prove_pic = ""
    # 易宝合作证明材料入账来源包含19:易宝时必填 文件类型F599；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    yb_cooperation_prove_pic = ""
    # 全渠道资金纸质协议文件协议类型为纸质时必填，文件类型F605；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    efp_paper_agreement_file = ""
    # 百度合作证明材料入账来源包含20:百度时必填 文件类型F616；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    bd_cooperation_prove_pic = ""
    # 主店商户号是否店群为是时必填
    main_store_huifu_id = ""
    # 顺丰合作证明材料入账来源包含21:顺丰时必填 文件类型F618；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    sf_cooperation_prove_pic = ""
    # 希音合作证明材料入账来源包含22:希音时必填 文件类型F619；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    xy_cooperation_prove_pic = ""
    # 高德合作证明材料入账来源包含23:高德时必填 文件类型F615；详见[文件类型说明](https://paas.huifu.com/open/doc/api/#/csfl/api_csfl_wjlx)；&lt;font color&#x3D;&quot;green&quot;&gt;示例值：57cc7f00-600a-33ab-b614-6221bbf2e530&lt;/font&gt;
    gd_cooperation_prove_pic = ""

    def post(self, extend_infos):
        """
        全渠道资金管理配置

        :param extend_infos: 扩展字段字典
        :return:
        """

        required_params = {
            "req_seq_id":self.req_seq_id,
            "req_date":self.req_date,
            "huifu_id":self.huifu_id,
            "upper_huifu_id":self.upper_huifu_id,
            "out_fee_huifuid":self.out_fee_huifuid,
            "out_order_acct_card":self.out_order_acct_card,
            "out_order_acct_open_fees":self.out_order_acct_open_fees,
            "business_model":self.business_model,
            "out_funds_gate_id":self.out_funds_gate_id,
            "sign_user_info":self.sign_user_info,
            "acct_source":self.acct_source,
            "dy_cooperation_prove_pic":self.dy_cooperation_prove_pic,
            "mt_cooperation_prove_pic":self.mt_cooperation_prove_pic,
            "ks_cooperation_prove_pic":self.ks_cooperation_prove_pic,
            "pdd_cooperation_prove_pic":self.pdd_cooperation_prove_pic,
            "xhs_cooperation_prove_pic":self.xhs_cooperation_prove_pic,
            "zfb_cooperation_prove_pic":self.zfb_cooperation_prove_pic,
            "wx_cooperation_prove_pic":self.wx_cooperation_prove_pic,
            "jd_cooperation_prove_pic":self.jd_cooperation_prove_pic,
            "elm_cooperation_prove_pic":self.elm_cooperation_prove_pic,
            "dw_cooperation_prove_pic":self.dw_cooperation_prove_pic,
            "wph_cooperation_prove_pic":self.wph_cooperation_prove_pic,
            "xc_cooperation_prove_pic":self.xc_cooperation_prove_pic,
            "zfbzl_cooperation_prove_pic":self.zfbzl_cooperation_prove_pic,
            "wxzl_cooperation_prove_pic":self.wxzl_cooperation_prove_pic,
            "ddjy_cooperation_prove_pic":self.ddjy_cooperation_prove_pic,
            "ty_cooperation_prove_pic":self.ty_cooperation_prove_pic,
            "tl_cooperation_prove_pic":self.tl_cooperation_prove_pic,
            "yb_cooperation_prove_pic":self.yb_cooperation_prove_pic,
            "efp_paper_agreement_file":self.efp_paper_agreement_file,
            "bd_cooperation_prove_pic":self.bd_cooperation_prove_pic,
            "main_store_huifu_id":self.main_store_huifu_id,
            "sf_cooperation_prove_pic":self.sf_cooperation_prove_pic,
            "xy_cooperation_prove_pic":self.xy_cooperation_prove_pic,
            "gd_cooperation_prove_pic":self.gd_cooperation_prove_pic
        }
        required_params.update(extend_infos)
        return request_post(V2_MERCHANT_BUSI_EFPCONFIG, required_params)
