from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from . import __version__


class PluginApp(AppConfig):
    name = "pretix_guestlist"
    verbose_name = "Guest List"

    class PretixPluginMeta:
        name = _("Guest List")
        author = "Praerie Festival"
        category = "FEATURE"
        description = _(
            "Smart guest list management for DJs and artists. "
            "Assign individual guest list quotas and let guests self-register."
        )
        visible = True
        version = __version__
        compatibility = "pretix>=2024.1.0"

    def ready(self):
        from . import signals  # NOQA
