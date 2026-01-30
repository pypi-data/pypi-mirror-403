import logging
from django.utils.translation import gettext_lazy as _

from pretix_worldlinedirect.payment import (
    WorldlineDirectMethod as SuperWorldlineDirectMethod,
    WorldlineDirectSettingsHolder,
)

logger = logging.getLogger("pretix_payonegopay")


class PAYONEGOPaySettingsHolder(WorldlineDirectSettingsHolder):
    identifier = "payonegopay_settings"
    verbose_name = _("PAYONE GOPay")
    is_enabled = False
    is_meta = True


class WorldlineDirectMethod(SuperWorldlineDirectMethod):
    identifier = "payonegopay"

    def get_endpoint_url(self, testmode):
        if testmode:
            return "https://payment.preprod.payone.com"
        else:
            return "https://payment.payone.com"
