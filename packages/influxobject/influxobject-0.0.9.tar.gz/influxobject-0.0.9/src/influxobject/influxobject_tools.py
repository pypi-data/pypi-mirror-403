"""influxobject_tools.py"""
# ----------------------------
#        PACKAGES
# ----------------------------


# ----------------------------
#        VARIABLES
# ----------------------------


# ----------------------------
#        FUNCTIONS
# ----------------------------
def celsius_to_fahrenheit(temperature_in_celsius) -> float:
    """celsius_to_fahrenheit: Convert celsius to fahrenheit"""
    return (temperature_in_celsius * 9 / 5) + 32


def celsius_to_kelvin(temperature_in_celsius) -> float:
    """celsius_to_kelvin: Convert celsius to kelvin"""
    return temperature_in_celsius + 273.15


def fahrenheit_to_celsius(temperature_in_fahrenheit) -> float:
    """fahrenheit_to_celsius: Convert fahrenheit to celsius"""
    return (temperature_in_fahrenheit - 32) * 5 / 9


def fahrenheit_to_kelvin(temperature_in_fahrenheit) -> float:
    """fahrenheit_to_celsius: Convert fahrenheit to celsius"""
    return ((temperature_in_fahrenheit - 32) * 5 / 9) + 273.15


# ----------------------------
#         CLASSES
# ----------------------------
