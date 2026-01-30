from django.utils.translation import gettext_lazy

from pretix_worldlinedirect import __compatibility__, __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_payonegopay"
    verbose_name = "PAYONE GOPay"

    class PretixPluginMeta:
        name = gettext_lazy("PAYONE GOPay")
        author = "pretix team"
        visible = True
        version = __version__
        compatibility = "pretix>=2025.9.0"
        category = "PAYMENT"
        picture = "pretix_payonegopay/logo.svg"
        compatibility = __compatibility__

        @property
        def description(self):
            t = gettext_lazy("Accept payments through PAYONE GOPay")
            t += '<div class="text text-info"><span class="fa fa-info-circle"></span> '
            t += gettext_lazy(
                "Also referred to as <em>Global Online Payment Services</em> or <em>PAYONE Direct</em>. Use this "
                "extension, if PAYONE has provided you with a <em>PSP ID</em>."
            )
            t += "</div>"

            return t

    def ready(self):
        from . import signals  # NOQA
