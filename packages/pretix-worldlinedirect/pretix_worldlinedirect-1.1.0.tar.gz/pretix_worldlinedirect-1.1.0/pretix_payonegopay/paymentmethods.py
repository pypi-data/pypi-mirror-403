from pretix_worldlinedirect.paymentmethods import (
    get_payment_method_classes,
    payment_methods as payment_methods_repo,
)

from .payment import PAYONEGOPaySettingsHolder, WorldlineDirectMethod

supported_methods = [
    "scheme",
    "visa",
    "amex",
    "mastercard",
    "maestro",
    "diners",
    "applepay",
    "googlepay",
    "ideal",
    "paypal",
    "p24",
    # "klarnapaynow",  # Klarna disabled upstream
    "wechatpay",
    "aplipayplus",
    "eps",
    "wero",
]
payment_methods = [
    item for item in payment_methods_repo if item.get("identifier") in supported_methods
]

payment_method_classes = get_payment_method_classes(
    "PAYONEGOPay", payment_methods, WorldlineDirectMethod, PAYONEGOPaySettingsHolder
)
