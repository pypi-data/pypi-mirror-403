from django.urls import include, path, re_path

from .views import ReturnView, webhook


def get_event_patterns(brand):
    return [
        re_path(
            r"^(?P<payment_provider>{})/".format(brand),
            include(
                [
                    path(
                        "return/<str:order>/<str:hash>/<str:payment>/",
                        ReturnView.as_view(),
                        name="return",
                    ),
                ]
            ),
        ),
    ]


def get_urlpatterns(brand):
    return [
        re_path(
            r"^_(?P<payment_provider>{})/".format(brand),
            include(
                [
                    path("webhook/", webhook, name="webhook"),
                ]
            ),
        )
    ]


event_patterns = get_event_patterns("worldlinedirect")
urlpatterns = get_urlpatterns("worldlinedirect")
