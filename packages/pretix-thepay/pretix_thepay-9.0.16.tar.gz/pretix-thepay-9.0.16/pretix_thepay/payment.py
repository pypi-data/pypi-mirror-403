"""
The Pay payment provider for Pretix.

This module implements the The Pay payment gateway integration for Pretix,
providing secure payment processing with The Pay REST API.
"""
import base64
import hashlib
import hmac
import logging
import requests
from collections import OrderedDict
from decimal import Decimal, ROUND_HALF_UP
from email.utils import formatdate
from typing import Dict, Optional, Any

from django import forms
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.models import Order, OrderPayment, OrderRefund
from pretix.base.payment import BasePaymentProvider, PaymentException

logger = logging.getLogger(__name__)


class ThePaySettingsForm(forms.Form):
    """
    Configuration form for The Pay payment provider settings.
    
    Collects merchant credentials and gateway configuration
    required for The Pay payment processing.
    """
    merchant_id = forms.CharField(
        label=_('Merchant ID'),
        help_text=_('Your The Pay merchant ID'),
        required=True,
        max_length=50,
    )
    project_id = forms.IntegerField(
        label=_('Project ID'),
        help_text=_('Your The Pay project ID'),
        required=True,
    )
    api_password = forms.CharField(
        label=_('API Password'),
        help_text=_('Your The Pay API password'),
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    language = forms.ChoiceField(
        label=_('Language'),
        help_text=_('Default language for payment gateway'),
        choices=[
            ('cs', 'Czech'),
            ('sk', 'Slovak'),
            ('en', 'English'),
        ],
        required=True,
        initial='en',
    )
    test_mode = forms.BooleanField(
        label=_('Test mode'),
        help_text=_('Enable test mode for development'),
        required=False,
        initial=False,
    )


class ThePay(BasePaymentProvider):
    """
    The Pay payment provider implementation for Pretix.
    
    Handles payment processing using The Pay REST API.
    """
    identifier = 'thepay'
    verbose_name = _('The Pay')
    public_name = _('The Pay')
    abort_pending_allowed = True
    refunds_allowed = True
    execute_payment_needs_user = True
    test_mode_message = _(
        'This payment provider can operate in demo mode. Enable "Test mode" in the settings to use The Pay demo environment.'
    )

    @property
    def settings_form_fields(self):
        # Preserve default fields (_enabled, fees, availability, etc.) and add ours
        fields = OrderedDict(super().settings_form_fields)
        fields.update(ThePaySettingsForm.base_fields)
        return fields

    def settings_content_render(self, request):
        return """
        <p>Configure your The Pay payment gateway settings.</p>
        <p>You need to:</p>
        <ul>
            <li>Obtain your merchant ID from The Pay</li>
            <li>Obtain your project ID from The Pay</li>
            <li>Configure your API password</li>
        </ul>
        <p><strong>Note:</strong> Enable test mode to use the demo environment.</p>
        """

    def payment_form_render(self, request, total, order=None) -> str:
        """
        Render payment form HTML.
        
        For The Pay, customers are redirected immediately to the gateway,
        so no form is displayed.
        """
        return ""

    def checkout_confirm_render(self, request, order=None, info_data=None) -> str:
        """
        Render checkout confirmation page HTML.
        
        Displays information about the The Pay payment method and
        informs customers they will be redirected to the gateway.
        """
        return _("You will be redirected to The Pay to complete your payment.")

    def payment_is_valid_session(self, request):
        """
        Validate payment session.
        
        Returns True as The Pay redirects immediately to the gateway
        without requiring session validation.
        """
        return True

    def execute_payment(self, request: HttpRequest, payment: OrderPayment) -> Optional[str]:
        """
        Execute the payment by creating a payment in The Pay and redirecting.
        """
        order = payment.order
        event = order.event

        settings_dict = self.settings
        merchant_id = settings_dict.get('merchant_id', '')
        project_id = settings_dict.get('project_id', '')
        api_password = settings_dict.get('api_password', '')
        language = settings_dict.get('language', 'en')
        test_mode = settings_dict.get('test_mode', False)

        if not merchant_id or not project_id or not api_password:
            raise PaymentException(_('The Pay is not configured properly.'))

        api_url = self._get_api_url(test_mode)

        # Create payment in The Pay
        try:
            payment_url = self._create_payment(
                payment=payment,
                order=order,
                merchant_id=merchant_id,
                project_id=project_id,
                api_password=api_password,
                api_url=api_url,
                language=language,
                return_url=request.build_absolute_uri(
                    reverse('plugins:pretix_thepay:return', kwargs={
                        'order': order.code,
                        'payment': payment.id,
                        'hash': payment.order.secret
                    })
                ),
                notify_url=request.build_absolute_uri(
                    reverse('plugins:pretix_thepay:notify', kwargs={
                        'order': order.code,
                        'payment': payment.id,
                        'hash': payment.order.secret
                    })
                ),
            )
        except Exception as e:
            logger.error(f'The Pay payment creation error: {e}', exc_info=True)
            raise PaymentException(_('Error preparing payment request.'))

        return payment_url

    def _create_payment(self, payment: OrderPayment, order: Order, merchant_id: str,
                       project_id: int, api_password: str, api_url: str,
                       language: str, return_url: str, notify_url: str) -> str:
        """
        Create a payment in The Pay and return the payment URL.
        
        Implementation based on The Pay API documentation:
        https://docs.thepay.eu/#tag/Payment-Creation
        
        Args:
            payment: OrderPayment instance
            order: Order instance
            merchant_id: The Pay merchant ID
            project_id: The Pay project ID
            api_password: The Pay API password
            api_url: The Pay API base URL
            language: Language code
            return_url: URL to redirect customer after payment
            notify_url: URL for server-to-server notification
            
        Returns:
            Payment URL to redirect customer to
            
        Note: Verify the following from The Pay documentation:
        - Exact API endpoint path (may be /api/v1/payments or similar)
        - Request format (JSON vs form-encoded)
        - Required vs optional parameters
        - Response format and field names
        """
        # Prepare payment data according to The Pay API format
        # Documentation: https://gate.thepay.cz/openapi.yaml
        # Note: project_id is in the URL path, not in the request body
        currency = self._get_order_currency(order)
        payment_data = {
            'amount': self._format_amount_minor_units(payment.amount, currency),
            'currency_code': self._get_currency_code(currency),
            'uid': f'pretix-{payment.id}-{order.code}',  # Unique identifier (must be unique per project)
            'order_id': order.code,
            'description_for_customer': f'Order {order.code}',
            'description_for_merchant': f'Pretix order {order.code} - Payment {payment.id}',
            'return_url': return_url,
            'notif_url': notify_url,
            'language_code': language,
            'is_customer_notification_enabled': False,
            # Sensible defaults matching The Pay API examples
            'can_customer_change_method': True,
        }
        
        # Add customer information (required by The Pay)
        customer_data = {}
        if order.invoice_address:
            name_parts = getattr(order.invoice_address, 'name_parts', None)
            if name_parts:
                customer_data['name'] = name_parts.get('given_name') or 'Customer'
                customer_data['surname'] = name_parts.get('family_name') or 'Customer'
            else:
                full_name = getattr(order.invoice_address, 'name', None)
                if full_name:
                    parts = full_name.split(None, 1)
                    customer_data['name'] = parts[0] if parts else 'Customer'
                    customer_data['surname'] = parts[1] if len(parts) > 1 else 'Customer'
                else:
                    customer_data['name'] = 'Customer'
                    customer_data['surname'] = 'Customer'
        else:
            customer_data['name'] = 'Customer'
            customer_data['surname'] = 'Customer'

        if order.email:
            customer_data['email'] = order.email
        elif order.invoice_address and getattr(order.invoice_address, 'phone', None):
            customer_data['phone'] = order.invoice_address.phone
        else:
            raise PaymentException(_('Customer email or phone is required for The Pay.'))

        if order.invoice_address:
            if getattr(order.invoice_address, 'phone', None):
                customer_data.setdefault('phone', order.invoice_address.phone)
            if getattr(order.invoice_address, 'country', None):
                country = getattr(order.invoice_address, 'country', '')
                country_code = getattr(country, 'alpha2', None) or str(country)
                city = getattr(order.invoice_address, 'city', '') or ''
                zipcode = getattr(order.invoice_address, 'zipcode', '') or ''
                street = getattr(order.invoice_address, 'street', '') or ''
                if country_code and city and zipcode and street:
                    customer_data['billing_address'] = {
                        'country_code': country_code,
                        'city': city,
                        'zip': zipcode,
                        'street': street,
                    }
        payment_data['customer'] = customer_data

        # Create payment via API
        # Documentation: https://gate.thepay.cz/openapi.yaml
        # Endpoint format (per spec): https://api.thepay.cz/v1/projects/{project_id}/payments?merchant_id=...
        # Demo: https://demo.api.thepay.cz/v1/projects/{project_id}/payments?merchant_id=...
        # Authentication: Signature and SignatureDate headers (not Basic Auth)
        try:
            base_url = api_url.rstrip('/')
            if 'demo.api.thepay.cz' in api_url:
                endpoint_url = f'https://demo.api.thepay.cz/v1/projects/{project_id}/payments'
            elif 'api.thepay.cz' in api_url or 'thepay.cz' in api_url:
                endpoint_url = f'https://api.thepay.cz/v1/projects/{project_id}/payments'
            else:
                endpoint_url = f'{base_url}/v1/projects/{project_id}/payments'
            
            # Generate authentication headers according to The Pay API spec
            # Signature = hash256(merchant_id + password + DateTime)
            # SignatureDate = current datetime in RFC7231 format
            signature_date = self._get_signature_date()
            signature = self._calculate_signature(merchant_id, api_password, signature_date)
            
            # Add merchant_id to query string (required by API)
            endpoint_url_with_params = f'{endpoint_url}?merchant_id={merchant_id}'
            
            response = requests.post(
                endpoint_url_with_params,
                json=payment_data,
                headers={
                    'Content-Type': 'application/json',
                    'Signature': signature,
                    'SignatureDate': signature_date,
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # The Pay returns payment URLs; uid is the one we provided
            payment_uid = payment_data.get('uid')
            if not payment_uid:
                logger.error('The Pay API response missing payment UID in request payload.')
                raise PaymentException(_('Invalid request data for The Pay.'))
            
            # Store payment_uid in payment.info for later status queries
            payment_info = self._get_payment_info(payment)
            payment_info['payment_uid'] = payment_uid
            if result.get('detail_url'):
                payment_info['detail_url'] = result.get('detail_url')
            if result.get('pay_url'):
                payment_info['pay_url'] = result.get('pay_url')
            self._save_payment_info(payment, payment_info)
            
            # Get payment URL from response or construct it
            payment_url = result.get('pay_url')
            if not payment_url:
                logger.error(f'The Pay API response: {response.text[:500]}')
                raise PaymentException(_('Invalid response from The Pay API: payment URL not found.'))
            
            return payment_url
            
        except requests.RequestException as e:
            logger.error(f'The Pay API request failed: {e}', exc_info=True)
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f'The Pay API error response: {e.response.text[:500]}')
            raise PaymentException(_('Failed to create payment in The Pay.'))

    def _get_signature_date(self) -> str:
        """
        Get current datetime in RFC7231 format for SignatureDate header.
        
        Format: "Mon, 23 Sep 2019 06:07:08 GMT"
        According to The Pay API spec: https://gate.thepay.cz/openapi.yaml
        
        Returns:
            Current datetime string in RFC7231 format
        """
        return formatdate(timeval=None, localtime=False, usegmt=True)

    def _get_payment_info(self, payment: OrderPayment) -> Dict[str, Any]:
        info = getattr(payment, 'info_data', None)
        if info is None:
            info = getattr(payment, 'info', None) or {}
        return info

    def _save_payment_info(self, payment: OrderPayment, info: Dict[str, Any]) -> None:
        if hasattr(payment, 'info_data'):
            payment.info_data = info
        else:
            payment.info = info
        payment.save(update_fields=['info'])
    
    def _calculate_signature(self, merchant_id: str, api_password: str, signature_date: str) -> str:
        """
        Calculate Signature header for The Pay API authentication.
        
        According to The Pay API spec: https://gate.thepay.cz/openapi.yaml
        Signature = hash256(merchant_id + password + DateTime)
        
        Format: merchant_idPasswordDatetime
        Example: "1passwordMon, 23 Sep 2019 06:07:08 GMT"
        
        Args:
            merchant_id: Merchant ID
            api_password: API password
            signature_date: Current datetime in RFC7231 format
            
        Returns:
            SHA256 hash as hexadecimal string
        """
        # Concatenate: merchant_id + password + DateTime
        signature_string = f'{merchant_id}{api_password}{signature_date}'
        
        # Calculate SHA256 hash
        signature_hash = hashlib.sha256(signature_string.encode('utf-8')).hexdigest()
        
        return signature_hash

    def _get_currency_code(self, currency: str) -> str:
        """
        Convert ISO 4217 currency code to The Pay format.
        
        Args:
            currency: ISO 4217 currency code (e.g., 'EUR', 'USD')
            
        Returns:
            Currency code (The Pay uses ISO 4217 codes)
        """
        # The Pay uses ISO 4217 currency codes
        return currency.upper()

    def _get_order_currency(self, order: Order) -> str:
        currency = getattr(order, 'currency', None)
        if currency:
            return currency
        if getattr(order, 'event', None) and getattr(order.event, 'currency', None):
            return order.event.currency
        raise PaymentException(_('Order currency is not available.'))

    def _get_api_url(self, test_mode: bool) -> str:
        return 'https://demo.api.thepay.cz' if test_mode else 'https://api.thepay.cz'

    def _get_currency_precision(self, currency: str) -> int:
        try:
            from babel.numbers import get_currency_precision
            return int(get_currency_precision(currency))
        except Exception as exc:
            logger.warning('Falling back to 2-decimal currency precision: %s', exc)
            return 2

    def _format_amount_minor_units(self, amount: Decimal, currency: str) -> str:
        precision = self._get_currency_precision(currency)
        factor = Decimal(10) ** precision
        minor_units = (amount * factor).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return str(int(minor_units))

    def _get_payment_status(self, payment_uid: str, merchant_id: str, project_id: int,
                            api_password: str, api_url: str) -> Optional[str]:
        """
        Query payment status from The Pay API.
        
        According to The Pay API spec: https://gate.thepay.cz/openapi.yaml
        Endpoint: GET /v1/projects/{project_id}/payments/{payment_uid}
        
        Args:
            payment_uid: Payment UID (the uid we sent when creating payment)
            merchant_id: Merchant ID
            project_id: Project ID
            api_password: API password
            api_url: API base URL
            
        Returns:
            Payment state ('paid', 'waiting_for_payment', 'expired', etc.) or None if error
        """
        try:
            # Construct endpoint URL
            if 'demo.api.thepay.cz' in api_url:
                endpoint_url = f'https://demo.api.thepay.cz/v1/projects/{project_id}/payments/{payment_uid}'
            elif 'api.thepay.cz' in api_url or 'thepay.cz' in api_url:
                endpoint_url = f'https://api.thepay.cz/v1/projects/{project_id}/payments/{payment_uid}'
            else:
                base_url = api_url.rstrip('/')
                endpoint_url = f'{base_url}/v1/projects/{project_id}/payments/{payment_uid}'
            
            # Generate authentication headers
            signature_date = self._get_signature_date()
            signature = self._calculate_signature(merchant_id, api_password, signature_date)
            
            # Add merchant_id to query string
            endpoint_url_with_params = f'{endpoint_url}?merchant_id={merchant_id}'
            
            response = requests.get(
                endpoint_url_with_params,
                headers={
                    'Content-Type': 'application/json',
                    'Signature': signature,
                    'SignatureDate': signature_date,
                },
                timeout=8
            )
            response.raise_for_status()
            result = response.json()
            
            # Return payment state
            return result.get('state') or result.get('status')
            
        except Exception as e:
            logger.error(f'Error querying The Pay payment status: {e}', exc_info=True)
            return None

    def payment_refund_supported(self, payment: OrderPayment) -> bool:
        info = self._get_payment_info(payment)
        payment_uid = info.get('payment_uid') or info.get('uid')
        supported = bool(payment_uid)
        if not supported:
            fallback_uid = f'pretix-{payment.id}-{payment.order.code}'
            info['payment_uid'] = fallback_uid
            self._save_payment_info(payment, info)
            payment_uid = fallback_uid
            supported = True
        if not supported:
            logger.warning(
                'The Pay refund not supported for payment %s: missing payment_uid in info_data (keys=%s)',
                payment.id,
                sorted(info.keys()),
            )
        return supported

    def payment_partial_refund_supported(self, payment: OrderPayment) -> bool:
        return self.payment_refund_supported(payment)

    # Compatibility with older Pretix versions
    def refund_supported(self, payment: OrderPayment) -> bool:
        return self.payment_refund_supported(payment)

    def partial_refund_supported(self, payment: OrderPayment) -> bool:
        return self.payment_partial_refund_supported(payment)

    def execute_refund(self, refund: OrderRefund):
        payment = refund.payment
        if not payment:
            raise PaymentException(_('No payment found for refund.'))

        info = self._get_payment_info(payment)
        payment_uid = info.get('payment_uid') or info.get('uid')
        if not payment_uid:
            payment_uid = f'pretix-{payment.id}-{payment.order.code}'
            info['payment_uid'] = payment_uid
            self._save_payment_info(payment, info)

        settings_dict = self.settings
        merchant_id = settings_dict.get('merchant_id', '')
        project_id = settings_dict.get('project_id', '')
        api_password = settings_dict.get('api_password', '')
        test_mode = settings_dict.get('test_mode', False)

        if not merchant_id or not project_id or not api_password:
            raise PaymentException(_('The Pay is not configured properly.'))

        api_url = self._get_api_url(test_mode).rstrip('/')
        currency = self._get_order_currency(payment.order)
        amount = self._format_amount_minor_units(refund.amount, currency)
        reason = (
            getattr(refund, 'reason', None) or
            getattr(refund, 'comment', None) or
            _('Refund from Pretix')
        )

        try:
            refund_info_before = self._get_refund_info(
                payment_uid, merchant_id, project_id, api_password, api_url
            )
            if not refund_info_before:
                raise PaymentException(_('Refund information is not available from The Pay.'))

            refund_currency = refund_info_before.get('currency')
            if refund_currency and refund_currency.upper() != currency.upper():
                raise PaymentException(_('Refund currency does not match payment currency.'))

            available_amount = int(refund_info_before.get('available_amount', 0))
            amount_int = int(amount)
            if amount_int < 1 or amount_int > available_amount:
                raise PaymentException(_('Refund amount exceeds available amount.'))

            self._request_refund(
                payment_uid=payment_uid,
                merchant_id=merchant_id,
                project_id=project_id,
                api_password=api_password,
                api_url=api_url,
                amount=amount_int,
                reason=str(reason),
            )

            refund_info_after = self._get_refund_info(
                payment_uid, merchant_id, project_id, api_password, api_url
            )
            self._store_refund_info(refund, refund_info_after or refund_info_before)

            refund_state = self._get_refund_state(refund_info_after or {}, amount_int)
            if refund_state in {'declined', 'failed'}:
                raise PaymentException(_('Refund was declined by The Pay.'))
            if refund_state == 'returned' or self._is_refund_visible(
                refund_info_before, refund_info_after, amount_int
            ):
                refund.done()
            else:
                refund.state = OrderRefund.REFUND_STATE_TRANSIT
                refund.save(update_fields=['state'])
                logger.info('The Pay refund is pending for refund %s', refund.id)
        except requests.RequestException as e:
            logger.error('The Pay refund request failed: %s', e, exc_info=True)
            if hasattr(e, 'response') and e.response is not None:
                logger.error('The Pay refund error response: %s', e.response.text[:500])
            raise PaymentException(_('Failed to create refund in The Pay.'))

    def _get_refund_info(self, payment_uid: str, merchant_id: str, project_id: int,
                         api_password: str, api_url: str) -> Optional[Dict[str, Any]]:
        try:
            if 'demo.api.thepay.cz' in api_url:
                endpoint_url = f'https://demo.api.thepay.cz/v1/projects/{project_id}/payments/{payment_uid}/refund'
            elif 'api.thepay.cz' in api_url or 'thepay.cz' in api_url:
                endpoint_url = f'https://api.thepay.cz/v1/projects/{project_id}/payments/{payment_uid}/refund'
            else:
                endpoint_url = f'{api_url}/v1/projects/{project_id}/payments/{payment_uid}/refund'

            signature_date = self._get_signature_date()
            signature = self._calculate_signature(merchant_id, api_password, signature_date)
            endpoint_url_with_params = f'{endpoint_url}?merchant_id={merchant_id}'

            response = requests.get(
                endpoint_url_with_params,
                headers={
                    'Content-Type': 'application/json',
                    'Signature': signature,
                    'SignatureDate': signature_date,
                },
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error('The Pay refund info request failed: %s', e, exc_info=True)
            if hasattr(e, 'response') and e.response is not None:
                logger.error('The Pay refund info error response: %s', e.response.text[:500])
            return None

    def _request_refund(self, payment_uid: str, merchant_id: str, project_id: int,
                        api_password: str, api_url: str, amount: int, reason: str) -> None:
        if 'demo.api.thepay.cz' in api_url:
            endpoint_url = f'https://demo.api.thepay.cz/v1/projects/{project_id}/payments/{payment_uid}/refund'
        elif 'api.thepay.cz' in api_url or 'thepay.cz' in api_url:
            endpoint_url = f'https://api.thepay.cz/v1/projects/{project_id}/payments/{payment_uid}/refund'
        else:
            endpoint_url = f'{api_url}/v1/projects/{project_id}/payments/{payment_uid}/refund'

        signature_date = self._get_signature_date()
        signature = self._calculate_signature(merchant_id, api_password, signature_date)
        endpoint_url_with_params = f'{endpoint_url}?merchant_id={merchant_id}'

        response = requests.post(
            endpoint_url_with_params,
            json={
                'amount': amount,
                'reason': reason,
            },
            headers={
                'Content-Type': 'application/json',
                'Signature': signature,
                'SignatureDate': signature_date,
            },
            timeout=30
        )
        response.raise_for_status()

    def _store_refund_info(self, refund: OrderRefund, data: Dict[str, Any]) -> None:
        info = getattr(refund, 'info_data', None)
        if info is None:
            info = getattr(refund, 'info', None) or {}
        info['thepay_refund_info'] = data
        if hasattr(refund, 'info_data'):
            refund.info_data = info
        else:
            refund.info = info
        refund.save(update_fields=['info'])

    def _get_refund_state(self, info: Dict[str, Any], amount: int) -> Optional[str]:
        partials = info.get('partial_refunds') or []
        for item in partials:
            if int(item.get('amount', 0)) == amount:
                return item.get('state')
        return None

    def _is_refund_visible(self, before: Dict[str, Any], after: Dict[str, Any],
                           amount: int) -> bool:
        try:
            if not after:
                return False
            before_amount = int(before.get('available_amount', 0))
            after_amount = int(after.get('available_amount', 0))
            if before_amount - after_amount >= amount:
                return True

            partials = after.get('partial_refunds') or []
            for item in partials:
                if int(item.get('amount', 0)) == amount:
                    return True
        except Exception:
            return False
        return False

    def _verify_signature(self, params: Dict[str, str], signature: str, api_password: str) -> bool:
        """
        Verify a signature from The Pay using HMAC-SHA256.
        
        Args:
            params: Request parameters (excluding signature)
            signature: Base64-encoded signature to verify
            api_password: API password for verification
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Sort parameters by key and build query string
            sorted_params = sorted(params.items())
            query_string = '&'.join(f'{k}={v}' for k, v in sorted_params if v)
            
            # Generate expected signature
            expected_signature = hmac.new(
                api_password.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            # Decode provided signature
            provided_signature = base64.b64decode(signature)
            
            # Compare signatures using constant-time comparison
            return hmac.compare_digest(expected_signature, provided_signature)
        except Exception as e:
            logger.error(f'Error verifying signature: {e}', exc_info=True)
            return False

    def payment_pending_render(self, request, payment: OrderPayment):
        """
        Render HTML for pending payment status.
        
        Args:
            request: HTTP request object
            payment: OrderPayment instance
            
        Returns:
            HTML string to display while payment is pending
        """
        info = self._get_payment_info(payment)
        pay_url = info.get('pay_url')
        if pay_url:
            return (
                f"{_('Your payment is being processed.')} "
                f"{_('If you paid by bank transfer, it can take a while. If card payment failed, you can retry here:')}"
                f" <a href=\"{pay_url}\">{_('Retry payment')}</a>"
            )
        return f"{_('Your payment is being processed.')} {_('Please wait...')}"

    def payment_control_render(self, request, payment: OrderPayment):
        """
        Render payment information in the control panel.
        
        Args:
            request: HTTP request object
            payment: OrderPayment instance
            
        Returns:
            HTML string displaying payment details
        """
        return f"""
        <dl class="dl-horizontal">
            <dt>{_('Payment ID')}</dt>
            <dd>{payment.id}</dd>
            <dt>{_('Status')}</dt>
            <dd>{payment.state}</dd>
        </dl>
        """

    def payment_control_render_short(self, payment: OrderPayment) -> str:
        info = self._get_payment_info(payment)
        payment_uid = info.get('payment_uid')
        if payment_uid:
            return f"{_('The Pay')} ({payment_uid[-6:]})"
        return _('The Pay')

    def payment_presale_render(self, payment: OrderPayment) -> str:
        return self.payment_control_render_short(payment)
