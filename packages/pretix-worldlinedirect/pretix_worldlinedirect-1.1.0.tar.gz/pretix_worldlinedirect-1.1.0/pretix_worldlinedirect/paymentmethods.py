from django import forms
from django.utils.translation import gettext_lazy as _

from .payment import (
    WorldlineDirectMethod,
    WorldlineDirectPayPal,
    WorldlineDirectScheme,
    WorldlineDirectSettingsHolder,
)

# https://docs.direct.worldline-solutions.com/en/payment-methods-and-features/
# 42 payment methods, updated 15.01.2025
# The method is the numeric ID that is being used by Worldline; the identifier is the
# static (!) name used to construct the python class names/selection form fields and should never change.
payment_methods = [
    {
        "method": 0,
        "identifier": "scheme",
        "type": "meta",
        "baseclass": WorldlineDirectScheme,
        "public_name": _("Credit card"),
        "verbose_name": _("Credit card"),
    },
    {
        "method": 1,
        "identifier": "visa",
        "type": "scheme",
        "public_name": _("Visa"),
        "verbose_name": _("Visa"),
    },
    {
        "method": 2,
        "identifier": "amex",
        "type": "scheme",
        "public_name": _("American Express"),
        "verbose_name": _("American Express"),
    },
    {
        "method": 3,
        "identifier": "mastercard",
        "type": "scheme",
        "public_name": _("Mastercard"),
        "verbose_name": _("Mastercard"),
    },
    {
        "method": 56,
        "identifier": "upi",
        "type": "scheme",
        "public_name": _("UPI - UnionPay International"),
        "verbose_name": _("UPI - UnionPay International"),
    },
    {
        "method": 117,
        "identifier": "maestro",
        "type": "scheme",
        "public_name": _("Maestro"),
        "verbose_name": _("Maestro"),
    },
    {
        "method": 125,
        "identifier": "jcb",
        "type": "scheme",
        "public_name": _("JCB"),
        "verbose_name": _("JCB"),
    },
    {
        "method": 128,
        "identifier": "discover",
        "type": "scheme",
        "public_name": _("Discover"),
        "verbose_name": _("Discover"),
    },
    {
        "method": 130,
        "identifier": "cb",
        "type": "scheme",
        "public_name": _("Cartes Bancaires"),
        "verbose_name": _("Cartes Bancaires"),
    },
    {
        "method": 132,
        "identifier": "diners",
        "type": "scheme",
        "public_name": _("Diners Club"),
        "verbose_name": _("Diners Club"),
    },
    {
        "method": 302,
        "identifier": "applepay",
        "type": "scheme",
        "public_name": _("Apple Pay"),
        "verbose_name": _("Apple Pay"),
    },
    {
        "method": 320,
        "identifier": "googlepay",
        "type": "scheme",
        "public_name": _("Google Pay"),
        "verbose_name": _("Google Pay"),
    },
    {
        "method": 771,
        "identifier": "sepadd",
        "public_name": _("SEPA Direct Debit"),
        "verbose_name": _("SEPA Direct Debit"),
    },
    {
        "method": 809,
        "identifier": "ideal",
        "public_name": _("iDEAL"),
        "verbose_name": _("iDEAL"),
    },
    {
        "method": 840,
        "identifier": "paypal",
        "baseclass": WorldlineDirectPayPal,
        "public_name": _("PayPal"),
        "verbose_name": _("PayPal"),
    },
    {
        "method": 900,
        "identifier": "wero",
        "public_name": _("WERO"),
        "verbose_name": _("WERO"),
    },
    {
        "method": 3012,
        "type": "scheme",
        "identifier": "bancontact",
        "public_name": _("Bancontact"),
        "verbose_name": _("Bancontact"),
    },
    {
        "method": 3103,
        "identifier": "bimplicado",
        "public_name": _("Bimpli CADO"),
        "verbose_name": _("Bimpli CADO"),
    },
    {
        "method": 3112,
        "identifier": "illicado",
        "public_name": _("Illicado"),
        "verbose_name": _("Illicado"),
    },
    {
        "method": 3116,
        "identifier": "spiritcadeau",
        "public_name": _("Spirit of Cadeau"),
        "verbose_name": _("Spirit of Cadeau"),
    },
    {
        "method": 3124,
        "identifier": "p24",
        "public_name": _("Przelewy24"),
        "verbose_name": _("Przelewy24"),
    },
    {
        "method": 3203,
        "identifier": "postfinancepay",
        "public_name": _("PostFinance Pay"),
        "verbose_name": _("PostFinance Pay"),
    },
    # No test account available and integration looks sketchy with multiple identifiers for the same thing...
    # Let's wait for someone to actually request this.
    # {
    #     "method": 3301,
    #     "identifier": "klarnapaynow",
    #     "public_name": _("Klarna Pay Now"),
    #     "verbose_name": _("Klarna Pay Now"),
    # },
    {
        "method": 5001,
        "identifier": "bizum",
        "public_name": _("Bizum"),
        "verbose_name": _("Bizum"),
    },
    {
        "method": 5100,
        "identifier": "cpay",
        "public_name": _("Cpay"),
        "verbose_name": _("Cpay"),
    },
    {
        "method": 5110,
        "identifier": "oney3x4x",
        "public_name": _("Oney 3x/4x"),
        "verbose_name": _("Oney 3x/4x"),
    },
    {
        "method": 5125,
        "identifier": "oneyfinancelong",
        "public_name": _("Oney Financement Long"),
        "verbose_name": _("Oney Financement Long"),
    },
    {
        "method": 5127,
        "identifier": "oneybankcard",
        "public_name": _("Oney Bank Card"),
        "verbose_name": _("Oney Bank Card"),
    },
    {
        "method": 5129,
        "identifier": "cofidis3x4x",
        "public_name": _("Cofidis 3x/4x"),
        "verbose_name": _("Cofidis 3x/4x"),
    },
    {
        "method": 5131,
        "identifier": "sofinco3x4x",
        "public_name": _("Sofinco 3x/4x"),
        "verbose_name": _("Sofinco 3x/4x"),
    },
    {
        "method": 5133,
        "identifier": "cetelem3x4x",
        "public_name": _("Cetelem 3x/4x"),
        "verbose_name": _("Cetelem 3x/4x"),
    },
    {
        "method": 5139,
        "identifier": "floapay",
        "public_name": _("FloaPay"),
        "verbose_name": _("FloaPay"),
    },
    {
        "method": 5402,
        "identifier": "mealvouchers",
        "public_name": _("Mealvouchers"),
        "verbose_name": _("Mealvouchers"),
    },
    {
        "method": 5403,
        "identifier": "cvconnect",
        "public_name": _("Chèque-Vacances Connect"),
        "verbose_name": _("Chèque-Vacances Connect"),
    },
    {
        "method": 5404,
        "identifier": "wechatpay",
        "public_name": _("WeChat Pay"),
        "verbose_name": _("WeChat Pay"),
    },
    {
        "method": 5405,
        "identifier": "aplipayplus",
        "public_name": _("Alipay+"),
        "verbose_name": _("Alipay+"),
    },
    {
        "method": 5406,
        "identifier": "eps",
        "public_name": _("EPS"),
        "verbose_name": _("EPS"),
    },
    {
        "method": 5407,
        "identifier": "twint",
        "public_name": _("Twint"),
        "verbose_name": _("Twint"),
    },
    {
        "method": 5408,
        "identifier": "banktransfer",
        "public_name": _("Bank Transfer"),
        "verbose_name": _("Bank Transfer by worldline"),
    },
    {
        "method": 5500,
        "identifier": "multibanco",
        "public_name": _("Multibanco"),
        "verbose_name": _("Multibanco"),
    },
    {
        "method": 5600,
        "identifier": "oneygc",
        "public_name": _("Oney Branded Gift Card"),
        "verbose_name": _("Oney Branded Gift Card"),
    },
    {
        "method": 5601,
        "identifier": "cadhoc",
        "public_name": _("Cadhoc"),
        "verbose_name": _("Cadhoc"),
    },
    {
        "method": 5700,
        "identifier": "intersolve",
        "public_name": _("Intersolve"),
        "verbose_name": _("Intersolve"),
    },
    {
        "method": 5908,
        "identifier": "mbway",
        "public_name": _("MB Way"),
        "verbose_name": _("MB Way"),
    },
]


def get_payment_method_classes(brand, payment_methods, baseclass, settingsholder):
    settingsholder.payment_methods_settingsholder = []
    for m in payment_methods:
        # We do not want meta methods like "scheme" in the settings holder
        if m.get("type") == "meta":
            continue
        settingsholder.payment_methods_settingsholder.append(
            (
                "method_{}".format(m["identifier"]),
                forms.BooleanField(
                    label="{} {}".format(
                        (
                            '<span class="fa fa-credit-card"></span>'
                            if m.get("type") == "scheme"
                            else ""
                        ),
                        m["verbose_name"],
                    ),
                    help_text=m["help_text"] if "help_text" in m else "",
                    required=False,
                ),
            )
        )
        if "baseclass" in m:
            for field in m["baseclass"].extra_form_fields:
                settingsholder.payment_methods_settingsholder.append(
                    ("method_{}_{}".format(m["identifier"], field[0]), field[1])
                )

    # We do not want the "scheme"-methods listed as a payment-method, since they are covered by the meta methods
    return [settingsholder] + [
        type(
            f'WorldlineDirect{"".join(m["identifier"].split())}',
            (
                # Custom baseclasses should always inherit from the brand-specific baseclass
                (
                    type(
                        f'WorldlineDirect{"".join(m["identifier"].split())}',
                        (m["baseclass"], baseclass),
                        {},
                    )
                    if "baseclass" in m
                    else baseclass
                ),
            ),
            {
                "identifier": "{payment_provider}_{payment_method}".format(
                    payment_method=m["identifier"], payment_provider=brand.lower()
                ),
                "verbose_name": _("{payment_method} via {payment_provider}").format(
                    payment_method=m["verbose_name"], payment_provider=brand
                ),
                "public_name": m["public_name"],
                "method": m["method"],
                "type": m.get("type"),
            },
        )
        for m in payment_methods
        if m.get("type") != "scheme"
    ]


payment_method_classes = get_payment_method_classes(
    "WorldlineDirect",
    payment_methods,
    WorldlineDirectMethod,
    WorldlineDirectSettingsHolder,
)
