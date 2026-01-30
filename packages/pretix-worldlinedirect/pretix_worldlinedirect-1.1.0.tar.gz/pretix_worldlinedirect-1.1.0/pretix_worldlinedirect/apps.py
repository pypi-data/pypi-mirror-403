from django.utils.translation import gettext_lazy

from . import __compatibility__, __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_worldlinedirect"
    verbose_name = "Worldline Direct"

    class PretixPluginMeta:
        name = gettext_lazy("Worldline Direct")
        author = "pretix team"
        description = gettext_lazy("Accept payments through Worldline Direct")
        visible = True
        version = __version__
        compatibility = "pretix>=2025.9.0"
        category = "PAYMENT"
        picture = "pretix_worldlinedirect/logo.svg"
        compatibility = __compatibility__

    def ready(self):
        from . import signals  # NOQA
