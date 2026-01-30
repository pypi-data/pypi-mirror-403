import hashlib
import importlib
import json
import logging
import re
from collections import OrderedDict
from decimal import Decimal
from django import forms
from django.core.cache import cache
from django.http import HttpRequest
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _  # NoQA
from onlinepayments.sdk.api_exception import ApiException
from onlinepayments.sdk.communicator import Communicator
from onlinepayments.sdk.defaultimpl.default_authenticator import DefaultAuthenticator
from onlinepayments.sdk.defaultimpl.default_connection import DefaultConnection
from onlinepayments.sdk.domain.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from onlinepayments.sdk.domain.refund_request import RefundRequest
from onlinepayments.sdk.factory import Factory
from onlinepayments.sdk.merchant.products.get_payment_products_params import (
    GetPaymentProductsParams,
)
from onlinepayments.sdk.meta_data_provider import MetaDataProvider
from pretix import settings
from pretix.base.decimal import round_decimal
from pretix.base.forms import SecretKeySettingsField
from pretix.base.forms.questions import guess_country_from_request
from pretix.base.models import Event, InvoiceAddress, Order, OrderPayment, OrderRefund
from pretix.base.payment import BasePaymentProvider, PaymentException, WalletQueries
from pretix.base.settings import SettingsSandbox
from pretix.helpers.urls import build_absolute_uri as build_global_uri
from pretix.multidomain.urlreverse import build_absolute_uri
from pretix.presale.views.cart import cart_session

from pretix_worldlinedirect.views import handle_refund

logger = logging.getLogger("pretix_worldlinedirect")


class WorldlineDirectSettingsHolder(BasePaymentProvider):
    identifier = "worldlinedirect_settings"
    verbose_name = _("Worldline Direct")
    is_enabled = False
    is_meta = True
    payment_methods_settingsholder = []

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox("payment", self.identifier.split("_")[0], event)

    @property
    def settings_form_fields(self):
        fields = [
            (
                "test_psp_id",
                forms.CharField(
                    label=_("Test PSP ID"),
                    required=False,
                ),
            ),
            (
                "test_api_key_id",
                forms.CharField(
                    label=_("Test API Key ID"),
                    required=False,
                ),
            ),
            (
                "test_api_key_secret",
                SecretKeySettingsField(
                    label=_("Test API Key Secret"),
                    required=False,
                ),
            ),
            (
                "live_psp_id",
                forms.CharField(
                    label=_("Live PSP ID"),
                    required=False,
                ),
            ),
            (
                "live_api_key_id",
                forms.CharField(
                    label=_("Live API Key ID"),
                    required=False,
                ),
            ),
            (
                "live_api_key_secret",
                SecretKeySettingsField(
                    label=_("Live API Key Secret"),
                    required=False,
                ),
            ),
        ]

        d = OrderedDict(
            fields
            + self.payment_methods_settingsholder
            + list(super().settings_form_fields.items())
        )
        d.move_to_end("_enabled", last=False)
        return d

    def settings_content_render(self, request: HttpRequest) -> str:
        ident = self.identifier.split("_")[0]

        return "<div class='alert alert-info'>%s<br /><code>%s</code></div>" % (
            _(
                "Please configure a Webhook to the following endpoint in order to automatically cancel orders when "
                "charges are refunded externally and to process asynchronous payment methods."
            ),
            build_global_uri(
                f"plugins:pretix_{ident}:webhook", kwargs={"payment_provider": ident}
            ),
        )


class WorldlineDirectMethod(BasePaymentProvider):
    identifier = ""
    method = ""
    type = ""

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox("payment", self.identifier.split("_")[0], event)

    @property
    def is_enabled(self) -> bool:
        if self.type == "meta":
            module = importlib.import_module(
                __name__.replace(
                    "worldlinedirect", self.identifier.split("_")[0]
                ).replace(".payment", ".paymentmethods")
            )
            for method in list(
                filter(lambda d: d.get("type") == "scheme", module.payment_methods)
            ):
                if self.settings.get("_enabled", as_type=bool) and self.settings.get(
                    "method_{}".format(method["identifier"]), as_type=bool
                ):
                    return True
            return False
        else:
            return self.settings.get("_enabled", as_type=bool) and self.settings.get(
                "method_{}".format(self.identifier.split("_")[1]), as_type=bool
            )

    def test_mode_message(self) -> str:
        if (
            self.settings.test_psp_id
            and self.settings.test_api_key_id
            and self.settings.test_api_key_secret
        ):
            return mark_safe(
                _(
                    "The Worldline Direct plugin is operating in test mode. You can use one of <a {args}>many test "
                    "cards</a> to perform a transaction. No money will actually be transferred."
                ).format(
                    args='href="https://docs.direct.worldline-solutions.com/en/integration/how-to-integrate/test-cases/index" target="_blank"'
                )
            )
        return None

    @property
    def settings_form_fields(self):
        return {}

    def is_allowed(self, request: HttpRequest, total: Decimal = None) -> bool:
        global_allowed = super().is_allowed(request, total)

        return global_allowed and self._payment_method_allowed(request, total)

    def payment_form_render(self, request, **kwargs) -> str:
        template = get_template("pretix_worldlinedirect/checkout_payment_form.html")
        ctx = {"request": request, "event": self.event, "settings": self.settings}
        return template.render(ctx)

    def checkout_confirm_render(
        self, request, order: Order = None, info_data: dict = None
    ) -> str:
        template = get_template("pretix_worldlinedirect/checkout_payment_confirm.html")
        ctx = {"request": request, "event": self.event, "settings": self.settings}
        return template.render(ctx)

    def payment_pending_render(
        self, request: HttpRequest, payment: OrderPayment
    ) -> str:
        template = get_template("pretix_worldlinedirect/pending.html")
        ctx = {
            "request": request,
            "event": self.event,
            "settings": self.settings,
            "provider": self,
            "order": payment.order,
            "payment": payment,
            "payment_info": payment.info_data,
            "payment_hash": hashlib.sha1(
                payment.order.secret.lower().encode()
            ).hexdigest(),
        }
        return template.render(ctx)

    def checkout_prepare(self, request, total):
        return True

    def payment_is_valid_session(self, request):
        return True

    def execute_payment(self, request: HttpRequest, payment: OrderPayment) -> str:
        payload = self.get_checkout_payload(request, payment)

        try:
            self._init_api(request.event.testmode)
            resp = self.client.hosted_checkout().create_hosted_checkout(
                CreateHostedCheckoutRequest().from_dictionary(payload)
            )
            payment.state = OrderPayment.PAYMENT_STATE_CREATED
            payment.info_data = resp.to_dictionary()
            payment.save(update_fields=["state", "info"])
        except ApiException as e:
            logger.exception("WorldlineDirect execute_payment")
            payment.fail(info=payload, log_data=e.response_body)

        if "redirectUrl" in payment.info_data:
            return payment.info_data["redirectUrl"]

        raise PaymentException(
            _(
                "We had trouble communicating with the payment service. Please try again and get "
                "in touch with us if this problem persists."
            )
        )

    def order_change_allowed(self, order: Order, request: HttpRequest = None) -> bool:
        global_allowed = super().order_change_allowed(order, request)

        return global_allowed and self._payment_method_allowed(
            request, order.pending_sum, order
        )

    def payment_control_render(
        self, request: HttpRequest, payment: OrderPayment
    ) -> str:
        template = get_template("pretix_worldlinedirect/control.html")
        ctx = {
            "request": request,
            "event": self.event,
            "settings": self.settings,
            "payment_info": payment.info_data,
            "order": payment.order,
            "provname": self.verbose_name,
        }
        return template.render(ctx)

    def payment_control_render_short(self, payment: OrderPayment) -> str:
        pi = payment.info_data or {}
        r = pi.get("id", pi.get("hostedCheckoutId", ""))
        return r

    def refund_control_render(self, request: HttpRequest, refund: OrderRefund) -> str:
        template = get_template("pretix_worldlinedirect/control.html")
        ctx = {
            "request": request,
            "event": self.event,
            "settings": self.settings,
            "payment_info": refund.info_data,
            "order": refund.order,
            "provname": self.verbose_name,
        }
        return template.render(ctx)

    def refund_control_render_short(self, refund: OrderRefund) -> str:
        ri = refund.info_data or {}
        r = ri.get("id", "")
        return r

    def payment_refund_supported(self, payment: OrderPayment) -> bool:
        return "id" in payment.info_data

    def payment_partial_refund_supported(self, payment: OrderPayment) -> bool:
        return "id" in payment.info_data

    def execute_refund(self, refund: OrderRefund):
        payment_info = refund.payment.info_data
        payload = self.get_refund_payload(refund)

        if not payment_info:
            raise PaymentException(_("No payment information found."))

        try:
            self._init_api(refund.order.testmode)
            resp = self.client.payments().refund_payment(
                payment_info.get("id"),
                RefundRequest().from_dictionary(payload),
            )
        except ApiException:
            logger.exception("WorldlineDirect execute_refund")
            refund.state = OrderRefund.REFUND_STATE_FAILED
            refund.execution_date = now()
            refund.info_data = resp.to_dictionary()
            refund.save(update_fields=["state", "execution_date", "info"])

            raise PaymentException(_("The refund has failed"))
        else:
            refund.info_data = resp.to_dictionary()
            refund.save(update_fields=["info"])
            handle_refund(refund)

    def api_payment_details(self, payment: OrderPayment):
        return {
            "id": payment.info_data.get("id", None),
        }

    def api_refund_details(self, refund: OrderRefund):
        return {
            "id": refund.info_data.get("id", None),
        }

    def matching_id(self, payment: OrderPayment):
        return payment.info_data.get("id", None)

    def refund_matching_id(self, refund: OrderRefund):
        return refund.info_data.get("id", None)

    def get_endpoint_url(self, testmode):
        if testmode:
            return "https://payment.preprod.direct.worldline-solutions.com"
        else:
            return "https://payment.direct.worldline-solutions.com"

    def _init_api(self, testmode):
        if testmode:
            authenticator = DefaultAuthenticator(
                self.settings.test_api_key_id, self.settings.test_api_key_secret
            )
            psp_id = self.settings.test_psp_id
        else:
            authenticator = DefaultAuthenticator(
                self.settings.live_api_key_id, self.settings.live_api_key_secret
            )
            psp_id = self.settings.live_psp_id

        communicator = Communicator(
            api_endpoint=self.get_endpoint_url(testmode),
            authenticator=authenticator,
            meta_data_provider=MetaDataProvider(settings.PRETIX_INSTANCE_NAME),
            connection=DefaultConnection(5000, 10000),
        )

        # Congratulations! Despite using Python and not Java, you now have a ProblemFactory.
        self.client = Factory.create_client_from_communicator(communicator).merchant(
            psp_id
        )

    def _amount_to_decimal(self, cents):
        places = settings.CURRENCY_PLACES.get(self.event.currency, 2)
        return round_decimal(float(cents) / (10**places), self.event.currency)

    def _decimal_to_int(self, amount):
        places = settings.CURRENCY_PLACES.get(self.event.currency, 2)
        return int(amount * 10**places)

    def _get_amount(self, payment):
        return self._decimal_to_int(payment.amount)

    def _guess_user_country(self, request: HttpRequest, order: Order = None):
        # We'll use guess_country_from_request() as a last resort fallback.
        # If we have an invoice address from an order, we'll use that.
        # If we don't have an order, we will try first to retrieve it from the
        # invoice address that might habe been provided during checkout.
        if order:
            try:
                return str(order.invoice_address.country)
            except InvoiceAddress.DoesNotExist:
                pass
        else:
            if not hasattr(request, "_checkout_flow_invoice_address"):
                cs = cart_session(request)
                iapk = cs.get("invoice_address")
                if not iapk:
                    request._checkout_flow_invoice_address = InvoiceAddress()
                else:
                    try:
                        request._checkout_flow_invoice_address = (
                            InvoiceAddress.objects.get(pk=iapk, order__isnull=True)
                        )
                    except InvoiceAddress.DoesNotExist:
                        request._checkout_flow_invoice_address = InvoiceAddress()

            if request._checkout_flow_invoice_address.country:
                return str(request._checkout_flow_invoice_address.country)

        return guess_country_from_request(request, self.event)

    def _get_payment_products(
        self, request: HttpRequest, order: Order, amount: Decimal
    ):
        self._init_api(request.event.testmode)

        country_code = self._guess_user_country(request, order)
        currency_code = self.event.currency
        amount = self._decimal_to_int(amount)
        checksum = hashlib.sha256(
            "".join(
                [
                    self.client._communicator.api_endpoint.netloc,
                    self.client._communicator.authenticator._DefaultAuthenticator__api_id_key,
                    self.client._communicator.authenticator._DefaultAuthenticator__secret_api_key,
                    self.client._ApiResource__path_context.get("merchantId"),
                    country_code,
                    currency_code,
                    str(amount),
                ]
            ).encode()
        ).hexdigest()
        cache_key_hash = (
            f'pretix_{self.identifier.split("_")[0]}_payment_products_{checksum}'
        )

        payment_products = cache.get(cache_key_hash)

        if not payment_products:
            params = GetPaymentProductsParams()
            params.country_code = country_code
            params.currency_code = currency_code
            params.amount = amount

            try:
                resp = self.client.products().get_payment_products(params)
                payment_products = [product.id for product in resp.payment_products]
                if payment_products:
                    cache.set(cache_key_hash, payment_products, 30)
            except ApiException:
                logger.exception("WorldlineDirect _get_payment_products")

        return payment_products

    def _payment_method_allowed(
        self, request: HttpRequest, amount: Decimal = None, order: Order = None
    ):
        if request.event.testmode:
            local_allowed = (
                self.settings.test_psp_id
                and self.settings.test_api_key_id
                and self.settings.test_api_key_secret
            )

        else:
            local_allowed = (
                self.settings.live_psp_id
                and self.settings.live_api_key_id
                and self.settings.live_api_key_secret
            )

        if local_allowed and self.method in self._get_payment_products(
            request, order, amount
        ):
            return True

        return False

    def statement_descriptor(self, payment, length=256):
        return "{event}-{code} {eventname}".format(
            event=self.event.slug.upper(),
            code=payment.order.code,
            eventname=re.sub("[^a-zA-Z0-9 ]", "", str(self.event.name)),
        )[:length]

    def get_checkout_payload(self, request: HttpRequest, payment: OrderPayment):
        ident = self.identifier.split("_")[0]

        # We could use the helper functions of the SDK here - but this makes it so much less legible.
        # We are also setting all PaymentMethodSpecificInputs to automatically capture the payment, since manual
        # captures display confusing/non-synchronized intermittent status messages.
        return {
            "cardPaymentMethodSpecificInput": {
                "authorizationMode": "SALE",
            },
            "redirectPaymentMethodSpecificInput": {
                "requiresApproval": False,
            },
            "mobilePaymentMethodSpecificInput": {
                "authorizationMode": "SALE",
            },
            "hostedCheckoutSpecificInput": {
                "cardPaymentMethodSpecificInput": {
                    "groupCards": True,
                },
                "isRecurring": False,
                "locale": payment.order.locale,
                "paymentProductFilters": {
                    "restrictTo": {
                        "products": [self.method],
                    },
                },
                "returnUrl": build_absolute_uri(
                    self.event,
                    f"plugins:pretix_{ident}:return",
                    kwargs={
                        "payment_provider": ident,
                        "order": payment.order.code,
                        "payment": payment.pk,
                        "hash": hashlib.sha1(
                            payment.order.secret.lower().encode()
                        ).hexdigest(),
                    },
                ),
                "showResultPage": False,
                "allowedNumberOfPaymentAttempts": 1,
            },
            "order": {
                "amountOfMoney": {
                    "amount": self._get_amount(payment),
                    "currencyCode": self.event.currency,
                },
                "references": {
                    "descriptor": self.statement_descriptor(payment),
                    "merchantReference": f"{self.event.slug.upper()}-{payment.full_id}",
                    "merchantParameters": json.dumps(
                        {
                            "organizer": self.event.organizer.pk,
                            "event": self.event.pk,
                            "payment": payment.pk,
                        }
                    ),
                },
                "customer": {
                    "contactDetails": {
                        "emailAddress": payment.order.email,
                    }
                },
            },
        }

    def get_refund_payload(self, refund: OrderRefund):
        # We could use the helper functions of the SDK here - but this makes it so much less legible.
        return {
            "amountOfMoney": {
                "amount": self._get_amount(refund),
                "currencyCode": self.event.currency,
            },
            "references": {
                "merchantReference": f"{self.event.slug.upper()}-{refund.full_id}",
                "merchantParameters": json.dumps(
                    {
                        "organizer": self.event.organizer.pk,
                        "event": self.event.pk,
                        "refund": refund.pk,
                    }
                ),
            },
        }


class WorldlineDirectScheme(WorldlineDirectMethod):
    @property
    def walletqueries(self):
        wallets = []

        if self.settings.get("method_applepay", as_type=bool):
            wallets.append(WalletQueries.APPLEPAY)

        if self.settings.get("method_googlepay", as_type=bool):
            wallets.append(WalletQueries.GOOGLEPAY)

        return wallets

    def _get_scheme_payment_product_candidates(self):
        module = importlib.import_module(
            __name__.replace("worldlinedirect", self.identifier.split("_")[0]).replace(
                ".payment", ".paymentmethods"
            )
        )

        return [
            x["method"]
            for x in list(
                filter(lambda d: d.get("type") == "scheme", module.payment_methods)
            )
            if self.settings.get("method_{}".format(x["identifier"]), as_type=bool)
        ]

    def get_checkout_payload(self, request: HttpRequest, payment: OrderPayment):
        data = super().get_checkout_payload(request, payment)

        candidates = self._get_scheme_payment_product_candidates()
        active_products = self._get_payment_products(
            request, payment.order, payment.amount
        )
        final_products = [
            candidate for candidate in candidates if candidate in active_products
        ]

        data["hostedCheckoutSpecificInput"]["paymentProductFilters"]["restrictTo"][
            "products"
        ] = final_products

        return data

    def _payment_method_allowed(
        self, request: HttpRequest, amount: Decimal = None, order: Order = None
    ):
        if request.event.testmode:
            local_allowed = (
                self.settings.test_psp_id
                and self.settings.test_api_key_id
                and self.settings.test_api_key_secret
            )

        else:
            local_allowed = (
                self.settings.test_psp_id
                and self.settings.live_api_key_id
                and self.settings.live_api_key_secret
            )

        if local_allowed:
            available_products = self._get_payment_products(request, order, amount)
            for candidate in self._get_scheme_payment_product_candidates():
                if candidate in available_products:
                    return True

        return False


class WorldlineDirectPayPal(WorldlineDirectMethod):
    extra_form_fields = []

    def get_checkout_payload(self, request: HttpRequest, payment: OrderPayment):
        data = super().get_checkout_payload(request, payment)

        data["redirectPaymentMethodSpecificInput"]["paymentProduct840SpecificInput"] = {
            "addressSelectionAtPayPal": True
        }

        return data
