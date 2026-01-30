import json
import requests
from dg_sdk.core.log_util import log_error, log_info
from dg_sdk.core.param_handler import pop_empty_value, sort_dict
from dg_sdk.core.rsa_utils import rsa_sign, rsa_design
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class ApiRequest:
    """
    网络请求类
    """
    request_url = ''
    product_id = ''
    sys_id = ''
    request_params = {}
    version = ''
    sdk_version = ''
    private_key = ''
    public_key = ''
    connect_timeout = ''
    need_sign = True
    need_verfy_sign = True

    @staticmethod
    def build(product_id, sys_id, private_key, public_key, request_url, request_params, sdk_version, need_sign,
              need_verfy_sign, connect_timeout=15):
        """
        初始化 网络请求类
        :param product_id: 产品号
        :param sys_id: 系统号
        :param private_key: 私钥
        :param public_key: 公钥
        :param request_url: 请求地址
        :param sdk_version: sdk_version
        :param need_sign: 是否需要签名
        :param need_verfy_sign: 是否需要验签
        :param request_params: 请求参数
        :param connect_timeout: 超时时间
        :return: 网络请求类
        """
        ApiRequest.product_id = product_id
        ApiRequest.sys_id = sys_id
        ApiRequest.request_url = request_url
        ApiRequest.private_key = private_key
        ApiRequest.public_key = public_key
        ApiRequest.sdk_version = sdk_version
        ApiRequest.request_params = request_params
        ApiRequest.need_sign = need_sign
        ApiRequest.need_verfy_sign = need_verfy_sign
        ApiRequest.connect_timeout = connect_timeout

    @staticmethod
    def post(request_file=None):
        return ApiRequest._request('post', request_file)

    @staticmethod
    def get():
        return ApiRequest._request('get', )

    @staticmethod
    def _build_request_info(url, params, files):
        """
        根据请求方式构造请求头和请求参数
        :param url: 请求地址
        :param params: 请求参数
        :param files: 请求文件
        :return: header 请求头 params 请求参数
        """

        # 获取商户密钥
        if not ApiRequest.private_key:
            raise RuntimeError('privite_key is none')
        # 构造请求头
        header = {"Content-Type": "application/json;charset=utf-8",
                  "sdk_version": "python_" + ApiRequest.sdk_version}
        if files:
            header = {
                "sdk_version": "python_" + ApiRequest.sdk_version}

        # 构造请求体
        body = dict()
        body["sys_id"] = ApiRequest.sys_id
        body["product_id"] = ApiRequest.product_id

        datastr = ""

        if params is not None:
            params = pop_empty_value(params)
            params = sort_dict(params=params)
            datastr = json.dumps(params, ensure_ascii=False, separators=(',', ':'))

        # 对请求参数进行加签
        sign = ''
        if ApiRequest.need_sign:
            flag, sign = rsa_sign(ApiRequest.private_key, datastr)
            if not flag:
                log_error('request to {}, sign error {} '.format(url, rsa_sign))

        # 将签名更新到请求头中
        body['sign'] = sign
        body['data'] = params

        return header, body

    @staticmethod
    def _request(method, files=None):
        """
        执行请求
        :param method: 请求方法类型

        :param files: 上传的文件
        :return: 网路请求返回的数据
        """

        request_url = ApiRequest.request_url

        header, params = ApiRequest._build_request_info(request_url, ApiRequest.request_params, files)
        log_info('request_params{} '.format(params))
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        if files:
            params["data"] = json.dumps(params["data"])
            resp = session.post(request_url, data=params, files=files, timeout=ApiRequest.connect_timeout,
                                headers=header)
        elif method == 'post':
            resp = session.post(request_url, json=params, files=files, timeout=ApiRequest.connect_timeout,
                                headers=header)
        else:
            resp = session.get(request_url, params, timeout=ApiRequest.connect_timeout, headers=header)
        log_info(
            'request to {}\nheader={}\nrequest_params{} \nresp is {}'.format(request_url, header, params, resp.text))
        resp.close()
        return ApiRequest._build_return_data(resp)

    @staticmethod
    def _build_return_data(resp):
        """
        解析网络返回
        :param resp: response
        :return: 解析处理后的网络返回
        """
        if resp.status_code != 200:
            log_error('status_code is ' + str(resp.status_code))
            return resp
        try:
            resp_json = json.loads(resp.text)
        except Exception as e:
            log_error('status_code is ' + str(resp.status_code))
            log_error(str(e))
            return resp.text
        # 服务端返回数据
        # 当业务请求成功时验证返回数据与签名
        data = resp_json.get('data', '')
        # 返回字段中的签名
        resp_sign = resp_json.get('sign', '')
        # 如果没有签名字段，直接返回内容，一般为404等
        if not resp_sign:
            return resp_json
        if ApiRequest.need_verfy_sign:
            if not ApiRequest.public_key:
                raise RuntimeError('public_key is none')
            # 验证返回数据与返回加签结果是否一致
            flag, info = verify_sign(resp_sign, data, ApiRequest.public_key)
            if not flag:
                # 如果验签失败，抛出异常
                log_error('check signature error !'.format(info))
                raise RuntimeError(info)
        return data


def verify_sign(sign, data, public_key):
    data = sort_dict(params=data)
    data_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return rsa_design(sign, data_str, public_key)
