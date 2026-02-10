"""
URL configuration for smart_home_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import MeView, UserViewSet
from devices.views import (
    DeviceHistoryView,
    DeviceTypeListView,
    DeviceViewSet,
    EnergyAnalysisExportCsvView,
    EnergyAnalysisView,
)
from logs_app.views import EmailAlertRuleViewSet, SystemLogViewSet
from mqtt_gateway.views import mqtt_status
from scenes.views import SceneRuleViewSet

router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"devices", DeviceViewSet, basename="device")
router.register(r"logs/system", SystemLogViewSet, basename="system-log")
router.register(r"alerts/email-rules", EmailAlertRuleViewSet, basename="email-alert-rule")
router.register(r"scenes", SceneRuleViewSet, basename="scene-rule")

urlpatterns = [
    path("admin/", admin.site.urls),
    # JWT 登录 / 刷新
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    # 业务 API
    path("api/", include(router.urls)),
    path(
        "api/devices/<int:pk>/history/",
        DeviceHistoryView.as_view(),
        name="device-history",
    ),
    path(
        "api/device-types/",
        DeviceTypeListView.as_view(),
        name="device-types",
    ),
    path(
        "api/energy/analysis/",
        EnergyAnalysisView.as_view(),
        name="energy-analysis",
    ),
    path(
        "api/energy/analysis/export.csv",
        EnergyAnalysisExportCsvView.as_view(),
        name="energy-analysis-export-csv",
    ),
    path("api/mqtt/status/", mqtt_status, name="mqtt-status"),
]
