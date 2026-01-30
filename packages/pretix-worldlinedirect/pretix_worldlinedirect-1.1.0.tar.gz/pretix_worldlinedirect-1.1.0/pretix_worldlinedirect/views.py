import hashlib
import json
import logging
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _  # NoQA
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_scopes import scopes_disabled
from json import JSONDecodeError
from onlinepayments.sdk.api_exception import ApiException
from onlinepayments.sdk.domain.capture_payment_request import CapturePaymentRequest
from pretix.base.models import Order, OrderPayment, OrderRefund
from pretix.base.payment import PaymentException
from pretix.multidomain.urlreverse import eventreverse

logger = logging.getLogger("pretix_worldlinedirect")


class WorldlineDirectOrderView:
    def dispatch(self, request, *args, **kwargs):
        try:
            self.order = request.event.orders.get(code=kwargs["order"])
            if (
                hashlib.sha1(self.order.secret.lower().encode()).hexdigest()
                != kwargs["hash"].lower()
            ):
                raise Http404("Unknown order")
        except Order.DoesNotExist:
            # Do a hash comparison as well to harden timing attacks
            if (
                "abcdefghijklmnopq".lower()
                == hashlib.sha1("abcdefghijklmnopq".encode()).hexdigest()
            ):
                raise Http404("Unknown order")
            else:
                raise Http404("Unknown order")
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def pprov(self):
        return self.payment.payment_provider

    @property
    def payment(self):
        return get_object_or_404(
            self.order.payments,
            pk=self.kwargs["payment"],
            provider__istartswith=self.kwargs["payment_provider"],
        )

    def _redirect_to_order(self):
        self.order.refresh_from_db()
        return redirect(
            eventreverse(
                self.request.event,
                "presale:event.order",
                kwargs={"order": self.order.code, "secret": self.order.secret},
            )
            + ("?paid=yes" if self.order.status == Order.STATUS_PAID else "")
        )


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(xframe_options_exempt, "dispatch")
class ReturnView(WorldlineDirectOrderView, View):
    def get(self, request, *args, **kwargs):
        try:
            handle_payment(self.payment)
        except PaymentException as e:
            messages.error(self.request, e)

        return self._redirect_to_order()


def handle_payment(payment):
    pprov = payment.payment_provider
    pprov._init_api(payment.order.testmode)

    # If we do not have a (payment) ID, we hopefully have a hosted checkout ID that we can use to retrieve
    # the payment ID
    if "id" not in payment.info_data:
        if "hostedCheckoutId" not in payment.info_data:
            logger.exception(
                "WorldlineDirect ReturnView: No hostedCheckoutId or PaymentId for %s"
                % payment.full_id
            )
            raise PaymentException(
                _(
                    "We had trouble communicating with the payment service. Please try again and get in touch "
                    "with us if this problem persists."
                )
            )
        else:
            try:
                hco = pprov.client.hosted_checkout().get_hosted_checkout(
                    payment.info_data["hostedCheckoutId"]
                )
            except ApiException:
                logger.exception("WorldlineDirect ReturnView/get_hosted_checkout")
                raise PaymentException(
                    _(
                        "We had trouble communicating with the payment service. Please try again and get in touch "
                        "with us if this problem persists."
                    )
                )

            if hco.created_payment_output.payment.id:
                payment_id = hco.created_payment_output.payment.id
            else:
                raise PaymentException(
                    _(
                        "We had trouble communicating with the payment service. Please try again and get in touch "
                        "with us if this problem persists."
                    )
                )
    else:
        payment_id = payment.info_data["id"]

    # If we made it this far, we should have the paymentId
    try:
        payment_data = pprov.client.payments().get_payment(payment_id)

        payment.info_data = payment_data.to_dictionary()
        payment.save(update_fields=["info"])
    except ApiException:
        logger.exception("WorldlineDirect ReturnView/get_payment")
        raise PaymentException(
            _(
                "We had trouble communicating with the payment service. Please try again and get in "
                "touch with us if this problem persists."
            )
        )

    if payment.info_data["status"] in ["CREATED"]:
        payment.state = OrderPayment.PAYMENT_STATE_CREATED
    elif payment.info_data["status"] in [
        "REDIRECTED",
        "PENDING_PAYMENT",
        "PENDING_COMPLETION",
        "AUTHORIZATION_REQUESTED",
        "CAPTURE_REQUESTED",
    ]:
        payment.state = OrderPayment.PAYMENT_STATE_PENDING
    elif payment.info_data["status"] in ["CANCELLED"]:
        payment.state = OrderPayment.PAYMENT_STATE_CANCELED
    elif payment.info_data["status"] in ["REJECTED", "REJECTED_CAPTURE"]:
        payment.fail()
    elif payment.info_data["status"] in ["PENDING_CAPTURE"]:
        # This is just preventative code that should not be in use with our
        # current integration.
        #
        # Should we ever decide to put it to use (through separate auth/capture),
        # then this might need some more locking.
        try:
            cpr = CapturePaymentRequest()
            cpr.is_final = True
            pprov.client.payments().capture_payment(payment_id, cpr)
        except ApiException:
            logger.exception("WorldlineDirect ReturnView/capture_payment")
            raise PaymentException(
                _(
                    "We had trouble communicating with the payment service. Please try again and get in "
                    "touch with us if this problem persists."
                )
            )
        else:
            payment.state = OrderPayment.PAYMENT_STATE_PENDING
            payment.save(update_fields=["state"])
            # Let's call ourselves again, this time the payment should have gone through.
            return handle_payment(payment, payment_id, pprov)
    elif payment.info_data["status"] in ["CAPTURED"]:
        payment.state = OrderPayment.PAYMENT_STATE_CONFIRMED
        payment.confirm()
    elif payment.info_data["status"] in ["REVERSED", "REFUND_REQUESTED", "REFUNDED"]:
        payment.state = OrderPayment.PAYMENT_STATE_REFUNDED

    payment.save(update_fields=["state"])


def handle_refund(refund: OrderRefund):
    pprov = refund.payment_provider
    pprov._init_api(refund.order.testmode)

    refund_id = refund.info_data["id"]

    try:
        refunds = pprov.client.payments().get_refunds(refund_id).to_dictionary()
    except ApiException:
        logger.exception("WorldlineDirect handle_refund/get_refunds")
        raise PaymentException(
            _(
                "We had trouble communicating with the payment service. Please try again and get in "
                "touch with us if this problem persists."
            )
        )

    refund_data = next(
        (refund for refund in refunds["refunds"] if refund["id"] == refund_id), {}
    )

    refund.info_data = refund_data
    refund.save(update_fields=["info"])

    if refund.info_data["status"] in ["REFUND_REQUESTED"]:
        refund.state = OrderRefund.REFUND_STATE_TRANSIT
    elif refund.info_data["status"] in ["REJECTED"]:
        refund.state = OrderRefund.REFUND_STATE_FAILED
    elif refund.info_data["status"] in ["REFUNDED"]:
        refund.done()

    refund.save(update_fields=["state"])


@csrf_exempt
@require_POST
@scopes_disabled()
def webhook(request, *args, **kwargs):
    # Not try/catching this on purpose; if they send us non-JSON, it should fail and now just acknowledge the webhook
    event_json = json.loads(request.body.decode("utf-8"))

    # On the other hand, we do catch the JSONDecodeError of the merchantParameters and payment retrieval, since a
    # merchant might not only use pretix with the same merchant account with different software that might not store
    # the data in this format.
    try:
        action = "refund" if "refund" in event_json else "payment"
        references = event_json[action][f"{action}Output"]["references"]
        merchant_parameters = json.loads(references["merchantParameters"])

        # Going extra specific here, even though just the payment_pk would be enough...
        if action == "refund":
            # Unfortunately, we do not get merchant_parameters filled with refund meta-data; so we have to get the
            # payment and then interfere the refund from there

            payment = OrderPayment.objects.get(
                order__event__organizer__pk=merchant_parameters["organizer"],
                order__event__pk=merchant_parameters["event"],
                pk=merchant_parameters["payment"],
            )

            merchant_reference = references.get("merchantReference").rsplit("-")

            if merchant_reference[-2] == "R":
                refund = payment.refunds.get(local_id=merchant_reference[-1])
            elif merchant_reference[-2] == "P":
                # This is probably a Dashboard-initiated, external refund.
                # And they are... special...
                #
                # - The first webhook to hit will have an ID of either a payment or the last
                #   refund - for example 123456789_6.
                # - The second to last webhooks will then have their proper ID - so in our
                #   example 123456789_7 - and that number will also be stable across all webhooks
                #   for that refund.
                #
                # So we are going a little bit creative about this...
                # - We will create an external_refund only if the status is "CREATED"
                # - We will only write updates to the refund, if there is an external_refund with ID of the
                #   "CREATED" webhook call
                # - As a result: We will ignore the first webhook-call that references the last payment/refund
                #   and that carries a "REFUNDED" message.

                if event_json[action]["status"] == "CREATED":
                    refund = payment.create_external_refund(
                        amount=event_json[action][f"{action}Output"]["amountOfMoney"][
                            "amount"
                        ],
                        info=json.dumps(event_json[action]),
                    )
                else:
                    for candidate in payment.refunds.all():
                        if candidate.info_data.get("id") == event_json[action]["id"]:
                            refund = candidate
                            break

                if not refund:
                    raise OrderRefund.DoesNotExist()
        elif action == "payment":
            payment = OrderPayment.objects.get(
                order__event__organizer__pk=merchant_parameters["organizer"],
                order__event__pk=merchant_parameters["event"],
                pk=merchant_parameters["payment"],
            )
        else:
            pass
    except (JSONDecodeError, OrderPayment.DoesNotExist, OrderRefund.DoesNotExist):
        pass
    else:
        if action == "refund":
            refund.order.log_action(
                "pretix_worldlinedirect.worldlinedirect.event", data=event_json
            )
            # We ignore PaymentExceptions here, since this is the webhook and the PaymentExceptions are used to communicate
            # error messages to the customer
            try:
                handle_refund(refund)
            except PaymentException:
                pass
        elif action == "payment":
            payment.order.log_action(
                "pretix_worldlinedirect.worldlinedirect.event", data=event_json
            )
            # We ignore PaymentExceptions here, since this is the webhook and the PaymentExceptions are used to communicate
            # error messages to the customer
            try:
                handle_payment(payment)
            except PaymentException:
                pass
        else:
            pass

    return HttpResponse("[accepted]", status=200)
