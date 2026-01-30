from dg_sdk.core.request_tools import request_post
from .PaymentCreateRequest import PaymentCreateRequest
from .PaymentQueryRequest import PaymentQueryRequest
from .PaymentCloseRequest import PaymentCloseRequest
from .PaymentCloseQueryRequest import PaymentCloseQueryRequest
from .PaymentRefundRequest import PaymentRefundRequest
from .PaymentRefundQueryRequest import PaymentRefundQueryRequest

# V4支付接口URL定义
V4_PAYMENT_CREATE = "/v4/trade/payment/create"
V4_PAYMENT_QUERY = "/v4/trade/payment/scanpay/query"
V4_PAYMENT_CLOSE = "/v2/trade/payment/scanpay/close"
V4_PAYMENT_CLOSE_QUERY = "/v2/trade/payment/scanpay/closequery"
V4_PAYMENT_REFUND = "/v4/trade/payment/scanpay/refund"
V4_PAYMENT_REFUND_QUERY = "/v4/trade/payment/scanpay/refundquery"


class Payment(object):

    @classmethod
    def create(cls, request: PaymentCreateRequest):
        """
        聚合支付下单
        """
        
        required_params = request.combileParams()

        return request_post(V4_PAYMENT_CREATE, required_params)
    
    @classmethod
    def query(cls, request: PaymentQueryRequest):
        """
        支付订单查询
        """
        
        required_params = request.combileParams()

        return request_post(V4_PAYMENT_QUERY, required_params)
    
    @classmethod
    def close(cls, request: PaymentCloseRequest):
        """
        交易关单
        """
        
        required_params = request.combileParams()

        return request_post(V4_PAYMENT_CLOSE, required_params)
    
    @classmethod
    def close_query(cls, request: PaymentCloseQueryRequest):
        """
        关单查询
        """
        
        required_params = request.combileParams()

        return request_post(V4_PAYMENT_CLOSE_QUERY, required_params)
    
    @classmethod
    def refund(cls, request: PaymentRefundRequest):
        """
        交易退款
        """
        
        required_params = request.combileParams()

        return request_post(V4_PAYMENT_REFUND, required_params)
    
    @classmethod
    def refund_query(cls, request: PaymentRefundQueryRequest):
        """
        退款查询
        """
        
        required_params = request.combileParams()

        return request_post(V4_PAYMENT_REFUND_QUERY, required_params)