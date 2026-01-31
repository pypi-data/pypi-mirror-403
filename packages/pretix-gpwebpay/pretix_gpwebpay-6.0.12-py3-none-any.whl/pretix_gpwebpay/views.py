"""
Views for handling GPWebPay payment gateway callbacks.

This module provides views for processing user redirects and server-to-server
notifications from the GPWebPay payment gateway, including signature verification
and payment status updates.
"""
import logging
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import escape
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_scopes import scopes_disabled
from pretix.base.models import Order, OrderPayment
from pretix.base.services import quotas

logger = logging.getLogger(__name__)

def _safe_order_url(order_obj: Order) -> str:
    if hasattr(order_obj, 'get_abandon_url'):
        return _safe_order_url(order_obj)
    if hasattr(order_obj, 'get_absolute_url'):
        return order_obj.get_absolute_url()
    return '/'


@method_decorator(csrf_exempt, name='dispatch')
class RedirectView(View):
    """
    Render an auto-submitting POST form to the GPWebPay gateway.
    """

    def get(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_redirect(request, order, payment, hash)

    def post(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_redirect(request, order, payment, hash)

    def _handle_redirect(self, request: HttpRequest, order: str, payment: int, hash: str):
        order_obj = None
        try:
            with scopes_disabled():
                payment_obj = get_object_or_404(
                    OrderPayment,
                    id=payment,
                    order__code=order,
                    order__secret=hash
                )
            order_obj = payment_obj.order
            event = order_obj.event

            provider = event.get_payment_providers().get('gpwebpay')
            if not provider:
                logger.error('GPWebPay provider not found')
                messages.error(request, _('Payment provider not configured.'))
                return redirect(_safe_order_url(order_obj))

            gateway_url = provider.get_gateway_url()

            params = provider.build_request_params(request, payment_obj)

            inputs = '\n'.join(
                f'<input type="hidden" name="{escape(str(k))}" value="{escape(str(v))}"/>'
                for k, v in params.items()
            )
            html = f"""
            <form id="gpwebpay-form" action="{escape(gateway_url)}" method="post" accept-charset="UTF-8">
                <p>{_('Redirecting to GPWebPay...')}</p>
                <p>{_('If you are not redirected automatically, click the button below.')}</p>
                {inputs}
                <button type="submit">{_('Continue to payment')}</button>
            </form>
            <script src="/static/pretix_gpwebpay/redirect.js"></script>
            """
            return HttpResponse(html)
        except Exception as e:
            logger.error(f'Error preparing GPWebPay redirect: {e}', exc_info=True)
            messages.error(request, _('Error preparing payment request.'))
            if order_obj is not None:
                try:
                    return redirect(_safe_order_url(order_obj))
                except Exception:
                    pass
            return HttpResponseBadRequest('Error preparing payment')


@method_decorator(csrf_exempt, name='dispatch')
class ReturnView(View):
    """
    Handle user redirect return from GPWebPay payment gateway.
    
    Processes the payment response when the customer is redirected back
    from the GPWebPay gateway after completing or canceling payment.
    """

    def get(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_response(request, order, payment, hash)

    def post(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_response(request, order, payment, hash)

    def _handle_response(self, request: HttpRequest, order: str, payment: int, hash: str):
        """
        Process GPWebPay return response.
        
        Verifies the payment signature, checks payment status codes,
        and updates the payment state accordingly.
        
        Args:
            request: HTTP request containing GPWebPay response parameters
            order: Order code
            payment: Payment ID
            hash: Order secret hash for validation
        """
        try:
            with scopes_disabled():
                payment_obj = get_object_or_404(
                    OrderPayment,
                    id=payment,
                    order__code=order,
                    order__secret=hash
                )
            order_obj = payment_obj.order
            event = order_obj.event

            # Get payment provider
            from pretix.base.models import Event
            provider = event.get_payment_providers().get('gpwebpay')
            if not provider:
                logger.error('GPWebPay provider not found')
                messages.error(request, _('Payment provider not configured.'))
                return redirect(_safe_order_url(order_obj))

            # Get settings
            settings_dict = provider.settings
            public_key_data = settings_dict.get('public_key', '')
            merchant_number = settings_dict.get('merchant_number', '')

            operation = request.GET.get('OPERATION', '') or request.POST.get('OPERATION', '')
            ordernumber = request.GET.get('ORDERNUMBER', '') or request.POST.get('ORDERNUMBER', '')
            merchantnumber = request.GET.get('MERCHANTNUMBER', '') or request.POST.get('MERCHANTNUMBER', '')
            prcode = request.GET.get('PRCODE', '') or request.POST.get('PRCODE', '')
            srcode = request.GET.get('SRCODE', '') or request.POST.get('SRCODE', '')
            resulttext = request.GET.get('RESULTTEXT', '') or request.POST.get('RESULTTEXT', '')
            digest = request.GET.get('DIGEST', '') or request.POST.get('DIGEST', '')
            digest1 = request.GET.get('DIGEST1', '') or request.POST.get('DIGEST1', '')
            if ' ' in digest or ' ' in digest1:
                digest = digest.replace(' ', '+')
                digest1 = digest1.replace(' ', '+')

            if ordernumber and str(payment_obj.id) != ordernumber:
                logger.error('GPWebPay order number mismatch: expected %s got %s', payment_obj.id, ordernumber)
                messages.error(request, _('Payment verification failed.'))
                return redirect(_safe_order_url(order_obj))

            if merchantnumber and merchant_number and merchantnumber != merchant_number:
                logger.error('GPWebPay merchant number mismatch: expected %s got %s', merchant_number, merchantnumber)
                messages.error(request, _('Payment verification failed.'))
                return redirect(_safe_order_url(order_obj))

            response_params = {}
            for field in provider.response_digest_fields:
                value = request.POST.get(field) or request.GET.get(field)
                if value not in (None, ''):
                    response_params[field] = value
            if 'OPERATION' not in response_params:
                response_params['OPERATION'] = operation or 'CREATE_ORDER'

            if public_key_data:
                if digest1:
                    response_digest = provider.build_response_digest1(response_params, merchant_number)
                    if not provider._verify_signature(response_digest, digest1, public_key_data):
                        logger.error('GPWebPay signature verification failed')
                        messages.error(request, _('Payment verification failed.'))
                        return redirect(_safe_order_url(order_obj))
                elif digest:
                    response_digest = provider.build_response_digest(response_params)
                    if not provider._verify_signature(response_digest, digest, public_key_data):
                        logger.error('GPWebPay signature verification failed')
                        messages.error(request, _('Payment verification failed.'))
                        return redirect(_safe_order_url(order_obj))
                else:
                    logger.error('GPWebPay response missing signature fields')
                    messages.error(request, _('Payment verification failed.'))
                    return redirect(_safe_order_url(order_obj))
            elif digest1 or digest:
                logger.warning('GPWebPay signature provided but public key not configured - skipping verification (less secure)')

            payment_obj.info = payment_obj.info or {}
            payment_obj.info['gpwebpay'] = {
                'operation': operation,
                'order_number': ordernumber,
                'prcode': prcode,
                'srcode': srcode,
                'resulttext': resulttext,
            }
            payment_obj.save(update_fields=['info'])

            if prcode == '0' and srcode == '0':
                if payment_obj.state == OrderPayment.PAYMENT_STATE_PENDING:
                    try:
                        payment_obj.confirm()
                        logger.info(f'GPWebPay payment {payment} confirmed for order {order}')
                        messages.success(request, _('Payment successful!'))
                        return redirect(order_obj.get_absolute_url())
                    except quotas.QuotaExceededException as e:
                        logger.error('GPWebPay quota exceeded for order %s: %s', order, e)
                        messages.error(request, str(e))
                        return redirect(_safe_order_url(order_obj))
                else:
                    return redirect(order_obj.get_absolute_url())
            else:
                error_msg = resulttext or _('Payment failed.')
                if payment_obj.state == OrderPayment.PAYMENT_STATE_PENDING:
                    payment_obj.fail(info={'error': error_msg})
                    logger.warning(f'GPWebPay payment {payment} failed for order {order}: {error_msg}')
                messages.error(request, error_msg)
                return redirect(_safe_order_url(order_obj))

        except Exception as e:
            logger.error(f'Error processing GPWebPay return: {e}', exc_info=True)
            messages.error(request, _('An error occurred while processing your payment.'))
            try:
                return redirect(_safe_order_url(order_obj))
            except:
                return HttpResponseBadRequest('Error processing payment')


@method_decorator(csrf_exempt, name='dispatch')
class NotifyView(View):
    """
    Handle server-to-server notification (IPN) from GPWebPay payment gateway.
    
    Processes asynchronous payment notifications sent by GPWebPay to confirm
    payment status independently of user redirect.
    """

    def get(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_notification(request, order, payment, hash)

    def post(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_notification(request, order, payment, hash)

    def _handle_notification(self, request: HttpRequest, order: str, payment: int, hash: str):
        """
        Process GPWebPay server notification.
        
        Verifies the notification signature, checks payment status codes,
        and updates the payment state. Returns HTTP 200 OK on success.
        
        Args:
            request: HTTP request containing GPWebPay notification parameters
            order: Order code
            payment: Payment ID
            hash: Order secret hash for validation
        """
        try:
            with scopes_disabled():
                payment_obj = get_object_or_404(
                    OrderPayment,
                    id=payment,
                    order__code=order,
                    order__secret=hash
                )
            order_obj = payment_obj.order
            event = order_obj.event

            # Get payment provider
            from pretix.base.models import Event
            provider = event.get_payment_providers().get('gpwebpay')
            if not provider:
                logger.error('GPWebPay provider not found')
                return HttpResponseBadRequest('Provider not configured')

            # Get settings
            settings_dict = provider.settings
            public_key_data = settings_dict.get('public_key', '')
            merchant_number = settings_dict.get('merchant_number', '')

            operation = request.GET.get('OPERATION', '') or request.POST.get('OPERATION', '')
            ordernumber = request.GET.get('ORDERNUMBER', '') or request.POST.get('ORDERNUMBER', '')
            merchantnumber = request.GET.get('MERCHANTNUMBER', '') or request.POST.get('MERCHANTNUMBER', '')
            prcode = request.GET.get('PRCODE', '') or request.POST.get('PRCODE', '')
            srcode = request.GET.get('SRCODE', '') or request.POST.get('SRCODE', '')
            resulttext = request.GET.get('RESULTTEXT', '') or request.POST.get('RESULTTEXT', '')
            digest = request.GET.get('DIGEST', '') or request.POST.get('DIGEST', '')
            digest1 = request.GET.get('DIGEST1', '') or request.POST.get('DIGEST1', '')
            if ' ' in digest or ' ' in digest1:
                digest = digest.replace(' ', '+')
                digest1 = digest1.replace(' ', '+')

            if ordernumber and str(payment_obj.id) != ordernumber:
                logger.error('GPWebPay order number mismatch: expected %s got %s', payment_obj.id, ordernumber)
                return HttpResponseBadRequest('Invalid order number')

            if merchantnumber and merchant_number and merchantnumber != merchant_number:
                logger.error('GPWebPay merchant number mismatch: expected %s got %s', merchant_number, merchantnumber)
                return HttpResponseBadRequest('Invalid merchant number')

            response_params = {}
            for field in provider.response_digest_fields:
                value = request.POST.get(field) or request.GET.get(field)
                if value not in (None, ''):
                    response_params[field] = value
            if 'OPERATION' not in response_params:
                response_params['OPERATION'] = operation or 'CREATE_ORDER'

            if public_key_data:
                if digest1:
                    response_digest = provider.build_response_digest1(response_params, merchant_number)
                    if not provider._verify_signature(response_digest, digest1, public_key_data):
                        logger.error('GPWebPay notification signature verification failed')
                        return HttpResponseBadRequest('Invalid signature')
                elif digest:
                    response_digest = provider.build_response_digest(response_params)
                    if not provider._verify_signature(response_digest, digest, public_key_data):
                        logger.error('GPWebPay notification signature verification failed')
                        return HttpResponseBadRequest('Invalid signature')
                else:
                    logger.error('GPWebPay notification missing signature fields')
                    return HttpResponseBadRequest('Invalid signature')
            elif digest1 or digest:
                logger.warning('GPWebPay notification signature provided but public key not configured - skipping verification (less secure)')

            payment_obj.info = payment_obj.info or {}
            payment_obj.info['gpwebpay'] = {
                'operation': operation,
                'order_number': ordernumber,
                'prcode': prcode,
                'srcode': srcode,
                'resulttext': resulttext,
            }
            payment_obj.save(update_fields=['info'])

            if prcode == '0' and srcode == '0':
                if payment_obj.state == OrderPayment.PAYMENT_STATE_PENDING:
                    try:
                        payment_obj.confirm()
                        logger.info(f'GPWebPay payment {payment} confirmed via notification for order {order}')
                    except quotas.QuotaExceededException as e:
                        logger.error('GPWebPay quota exceeded for order %s: %s', order, e)
                        return HttpResponseBadRequest('Quota exceeded')
            else:
                if payment_obj.state == OrderPayment.PAYMENT_STATE_PENDING:
                    payment_obj.fail(info={'error': resulttext or 'Payment failed'})
                    logger.warning(f'GPWebPay payment {payment} failed via notification for order {order}')

            return HttpResponse('OK')

        except Exception as e:
            logger.error(f'Error processing GPWebPay notification: {e}', exc_info=True)
            return HttpResponseBadRequest('Error processing notification')
