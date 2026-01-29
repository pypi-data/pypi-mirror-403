"""
Django views for PayTechUZ.
"""
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from paytechuz.core.exceptions import MissingLicenseKeyError, InvalidLicenseKeyError

from .webhooks import PaymeWebhook, ClickWebhook, UzumWebhook, PaynetWebhook

logger = logging.getLogger(__name__)


def _license_error_response(error: Exception) -> JsonResponse:
    """Return JSON error response for license errors."""
    is_missing = isinstance(error, MissingLicenseKeyError)

    return JsonResponse({
        "error": {
            "code": "missing_license_key" if is_missing else "invalid_license_key",
            "message": "PAYTECH_LICENSE_API_KEY not found" if is_missing else "Invalid PAYTECH_LICENSE_API_KEY",
            "details": {
                "get_api_key": "https://pay-tech.uz/console",
                "configuration": {
                    "option_1": "Set PAYTECH_LICENSE_API_KEY in .env file",
                    "option_2": "Set PAYTECH_LICENSE_API_KEY in Django settings.py"
                },
                "support": "Contact @muhammadali_me on Telegram"
            }
        }
    }, status=503)


class LicenseErrorMixin:
    """Mixin to handle license errors gracefully."""

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)

        @csrf_exempt
        def wrapped_view(request, *args, **kwargs):
            try:
                return view(request, *args, **kwargs)
            except (MissingLicenseKeyError, InvalidLicenseKeyError) as e:
                logger.error(f"License error: {e}")
                return _license_error_response(e)

        return wrapped_view


@method_decorator(csrf_exempt, name='dispatch')
class BasePaymeWebhookView(LicenseErrorMixin, PaymeWebhook):
    """
    Default Payme webhook view.

    This view handles webhook requests from the Payme payment system.
    You can extend this class and override the event methods to customize
    the behavior.

    Example:
    ```python
    from paytechuz.integrations.django.views import PaymeWebhookView

    class CustomPaymeWebhookView(PaymeWebhookView):
        def successfully_payment(self, params, transaction):
            # Your custom logic here
            print(f"Payment successful: {transaction.transaction_id}")

            # Update your order status
            order = Order.objects.get(id=transaction.account_id)
            order.status = 'paid'
            order.save()
    ```
    """

    def successfully_payment(self, params, transaction):
        """
        Called when a payment is successful.

        Args:
            params: Request parameters
            transaction: Transaction object
        """
        logger.info(f"Payme payment successful: {transaction.transaction_id}")

    def cancelled_payment(self, params, transaction):
        """
        Called when a payment is cancelled.

        Args:
            params: Request parameters
            transaction: Transaction object
        """
        logger.info(f"Payme payment cancelled: {transaction.transaction_id}")

    def get_check_data(self, params, account):
        """
        Override this method to return extra data in check response.
        By default returns empty dict.
        """


@method_decorator(csrf_exempt, name='dispatch')
class BaseClickWebhookView(LicenseErrorMixin, ClickWebhook):
    """
    Default Click webhook view.

    This view handles webhook requests from the Click payment system.
    You can extend this class and override the event methods to customize
    the behavior.

    Example:
    ```python
    from paytechuz.integrations.django.views import ClickWebhookView

    class CustomClickWebhookView(ClickWebhookView):
        def successfully_payment(self, params, transaction):
            # Your custom logic here
            print(f"Payment successful: {transaction.transaction_id}")

            # Update your order status
            order = Order.objects.get(id=transaction.account_id)
            order.status = 'paid'
            order.save()
    ```
    """

    def successfully_payment(self, params, transaction):
        """
        Called when a payment is successful.

        Args:
            params: Request parameters
            transaction: Transaction object
        """
        logger.info(f"Click payment successful: {transaction.transaction_id}")

    def cancelled_payment(self, params, transaction):
        """
        Called when a payment is cancelled.

        Args:
            params: Request parameters
            transaction: Transaction object
        """
        logger.info(f"Click payment cancelled: {transaction.transaction_id}")



@method_decorator(csrf_exempt, name='dispatch')
class BaseUzumWebhookView(LicenseErrorMixin, UzumWebhook):
    """
    Default Uzum webhook view.

    This view handles webhook requests from the Uzum payment system.
    You can extend this class and override the event methods to customize
    the behavior.

    Example:
    ```python
    from paytechuz.integrations.django.views import BaseUzumWebhookView

    class CustomUzumWebhookView(BaseUzumWebhookView):
        def successfully_payment(self, params, transaction):
            # Your custom logic here
            print(f"Payment successful: {transaction.transaction_id}")

            # Update your order status
            order = Order.objects.get(id=transaction.account_id)
            order.status = 'paid'
            order.save()
    ```
    """

    def successfully_payment(self, params, transaction):
        """
        Called when a payment is successful.
        """
        logger.info(f"Uzum payment successful: {transaction.transaction_id}")

    def cancelled_payment(self, params, transaction):
        """
        Called when a payment is cancelled.
        """
        logger.info(f"Uzum payment cancelled: {transaction.transaction_id}")

    def get_check_data(self, params, account):
        """
        Override this method to return extra data in check response.
        By default returns empty dict.
        """


@method_decorator(csrf_exempt, name='dispatch')
class BasePaynetWebhookView(LicenseErrorMixin, PaynetWebhook):
    """
    Default Paynet webhook view.

    This view handles webhook requests from the Paynet payment system.
    You can extend this class and override the event methods to customize
    the behavior.

    Example:
    ```python
    from paytechuz.integrations.django.views import BasePaynetWebhookView

    class CustomPaynetWebhookView(BasePaynetWebhookView):
        def successfully_payment(self, params, transaction):
            # Your custom logic here
            print(f"Payment successful: {transaction.transaction_id}")

            # Update your order status
            order = Order.objects.get(id=transaction.account_id)
            order.status = 'paid'
            order.save()
    ```
    """

    def successfully_payment(self, params, transaction):
        """
        Called when a payment is successful.
        """
        logger.info(f"Paynet payment successful: {transaction.transaction_id}")

    def cancelled_payment(self, params, transaction):
        """
        Called when a payment is cancelled.
        """
        logger.info(f"Paynet payment cancelled: {transaction.transaction_id}")

    def get_check_data(self, params, account):
        """
        Override this method to return extra data in check response.
        By default returns empty dict.
        """
