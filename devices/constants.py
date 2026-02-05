from django.db import models


class DeviceType(models.TextChoices):
    TEMPERATURE_HUMIDITY = "TEMP_HUMI", "温湿度传感器"
    LIGHT = "LIGHT", "光照传感器"
    PRESSURE = "PRESSURE", "气压传感器"
    LAMP_SWITCH = "LAMP_SWITCH", "灯具开关"
    AC_SWITCH = "AC_SWITCH", "空调开关"
    PIR = "PIR", "人体感应"
    FAN_SWITCH = "FAN_SWITCH", "风扇开关"
    SMOKE = "SMOKE", "烟雾传感器"

