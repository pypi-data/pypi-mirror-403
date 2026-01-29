"""influxpoint.py



REQUIREMENTS:
    import logging
    from typing import Dict, Optional, Union
    from datetime import datetime
    import re



"""

# ----------------------------
#        PACKAGES
# ----------------------------
import logging
import re
from datetime import datetime
from typing import Optional, Union

# ----------------------------
#        VARIABLES
# ----------------------------


# ----------------------------
#        FUNCTIONS
# ----------------------------


def convert_to_seconds(timestamp: int) -> float:
    """convert_to_seconds: Convert timestamp to seconds

    INPUT:
        timestamp = original timestamp, an int

    OUTPUT:
        timestamp = converted timestamp, a float


    """
    length = len(str(timestamp))
    if length >= 19:  # nanoseconds
        logging.warning("Timestamp is converted to seconds, precision is lost.")
        return timestamp / 1_000_000_000
    elif length >= 16:  # microseconds
        logging.warning("Timestamp is converted to seconds, precision is lost.")
        return timestamp / 1_000_000
    elif length >= 13:  # milliseconds
        logging.warning("Timestamp is converted to seconds, precision is lost.")
        return timestamp / 1_000
    elif length >= 10:  # seconds
        return timestamp
    else:
        raise ValueError("Timestamp value is too short to be valid")


# ----------------------------
#         CLASSES
# ----------------------------


class InfluxPoint:
    def __init__(self) -> None:
        """init: Initialise class

        INPUT:
            None

        OUTPUT:
            None, initialise self.measurement
                            self.tags
                            self.fields
                            self.timestamp


        """
        self.measurement: Optional[str] = None
        self.tags: dict[str, str] = {}
        self.fields: dict[str, Union[int, float, str]] = {}
        self.timestamp: Optional[datetime] = datetime.now()

    def set_measurement(self, measurement: str) -> None:
        """set_measurement: Set measurement

        INPUT:
            measurement = measurement value to set, of type str

        OUTPUT:
            None, sets self.measurement or raises TypeError


        """
        if not isinstance(measurement, str):
            raise TypeError(
                f"Measurement must be of type str, not {type(measurement).__name__}"
            )
        self.measurement = measurement

    def set_tags(self, tags: dict[str, str]) -> None:
        """set_tags: Set tags"""
        for k, v in tags.items():
            if not isinstance(v, str):
                raise TypeError(
                    f"Value for '{k}' must be of type str, not {type(v).__name__}"
                )
        self.tags = tags

    def set_fields(self, fields: dict[str, Union[int, float, str]]) -> None:
        """set_fields: Set fields"""
        for k, v in fields.items():
            if not isinstance(v, (int, float, str)):
                raise TypeError(
                    f"Value for '{k}' must be int, float, or str, "
                    f"not {type(v).__name__}"
                )
        self.fields = fields

    def set_timestamp(self, timestamp: datetime) -> None:
        """set_timestamp: Set timestamp"""
        if not isinstance(timestamp, datetime):
            if isinstance(timestamp, int):
                timestamp = datetime.fromtimestamp(convert_to_seconds(timestamp))
            else:
                raise ValueError(
                    "Timestamp must be either numeric (seconds) or a datetime object"
                )
        self.timestamp = timestamp

    def to_line_protocol(self) -> str:
        """set_timestamp: Set timestamp"""
        self.validate()
        tags = ",".join([f"{k}={v}" for k, v in self.tags.items()])
        fields = ",".join([f"{k}={v}" for k, v in self.fields.items()])
        return f"{self.measurement},{tags} {fields} {int(self.timestamp.timestamp())}"

    def __str__(self) -> str:
        """str: Get line protocol"""
        return self.to_line_protocol()

    # ----------------------------
    #   Add or remove tags
    # ----------------------------
    def add_tag(self, key: str, value: str) -> None:
        """add_tag: Add tag"""
        if not isinstance(value, (int, float, str)):
            raise TypeError(
                f"Value for '{key}' must be int, float, or str, "
                f"not {type(value).__name__}"
            )
        self.tags[key] = value

    def remove_tag(self, key: str) -> None:
        """remove_tag: Remove tag"""
        del self.tags[key]

    # ----------------------------
    #   Add or remove fields
    # ----------------------------
    def add_field(self, key: str, value: Union[int, float, str]) -> None:
        """add_field: Add field"""
        if not isinstance(value, (int, float, str)):
            raise TypeError(
                f"Value for '{key}' must be int, float, or str, "
                f"not {type(value).__name__}"
            )
        self.fields[key] = value

    def remove_field(self, key: str) -> None:
        """remove_field: Remove field timestamp"""
        del self.fields[key]

    # ----------------------------
    #   Add specific tags if needed
    # ----------------------------
    def set_entity_tag(self, entity: str) -> None:
        """set_entity_tag: Set entity tag

        Add an entity tag to the InfluxPoint for example a weather station,
        bioreactor, storage instance.

        INPUT:
            entity: The entity to add as a tag.

        OUTPUT:
            None, raises TypeError: If the entity is not a string.

        """
        if not isinstance(entity, str):
            raise TypeError(f"Entity must be of type str, not {type(entity).__name__}")
        self.add_tag("entity", entity)

    def get_entity_tag(self) -> Optional[str]:
        """
            Get the entity tag from the InfluxPoint.
        :return: The entity tag if it exists, otherwise None.
        """
        if not self.tags:
            return None
        if "entity" not in self.tags:
            logging.warning("Entity tag is not set, returning None")
            return None
        return self.tags.get("entity")

    def set_value(self, value: Union[int, float]) -> None:
        """set_value: Set the value field for the InfluxPoint.

        This is a convenience method to set a primary value field in the InfluxPoint.
        :param value: The value to set in the fields.
        :raises TypeError: If the value is not of type int, float.
        """
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"Value must be of type int, float, not {type(value).__name__}"
            )
        self.add_field("value", value)

    def get_value(self) -> Optional[Union[int, float]]:
        """
        Get the value field from the InfluxPoint.
        :return: The value field if it exists, otherwise None.
        """
        if not self.fields:
            return None
        if "value" not in self.fields:
            logging.warning("Value field is not set, returning None")
            return None
        return self.fields.get("value")

    def set_metric(self, metric: str) -> None:
        """
        Set the metric tag for the InfluxPoint to identify the type of data.
        Useful for categorizing the data, such as temperature, humidity, etc.
        :param metric: The metric to set as a tag.
        :raises TypeError: If the metric is not a string.
        """
        if not isinstance(metric, str):
            raise TypeError(f"Metric must be of type str, not {type(metric).__name__}")
        self.add_tag("metric", metric)

    def get_metric(self) -> Optional[str]:
        """
        Get the metric tag from the InfluxPoint.
        :return: The metric tag if it exists, otherwise None.
        """
        if not self.tags:
            return None
        if "metric" not in self.tags:
            logging.warning("Metric tag is not set, returning None")
            return None
        return self.tags.get("metric")

    def set_unit(self, unit: str) -> None:
        """
        Set the unit tag for the InfluxPoint to specify the unit of measurement.
        :param unit: The unit to set as a tag.
        :raises TypeError: If the unit is not a string.
        """
        if not isinstance(unit, str):
            raise TypeError(f"Unit must be of type str, not {type(unit).__name__}")
        self.add_tag("unit", unit)

    def get_unit(self) -> Optional[str]:
        """get_unit: Get the unit tag from the InfluxPoint.

        INPUT:
            None

        OUTPUT:
            :return: The unit tag if it exists, otherwise None.

        """
        if not self.tags:
            return None
        if "unit" not in self.tags:
            logging.warning("Unit tag is not set, returning None")
            return None
        return self.tags.get("unit")

    def validate(self) -> None:
        """validate: Validate the line protocol

        INPUT:
            None

        OUTPUT:
            None, raise valueerror if line is missing
                   measurement, timestamp, fields or
                   tags

        """
        errors = []

        # -------------------------
        # CHECK
        if self.measurement is None:
            errors.append("Measurement is not set")

        if self.timestamp is None:
            errors.append("Timestamp is not set")

        if not self.fields:
            errors.append("Fields are not set")

        if not self.tags:
            errors.append("Tags are not set")

        # -------------------------
        # IF errors are not empty
        if errors:
            raise ValueError(", ".join(errors))

    # ----------------------------
    #   to and from json
    # ----------------------------
    def to_json(
        self,
    ) -> dict[str, Union[str, dict[str, str], dict[str, Union[int, float, str]], str]]:
        """to_json: Convert point to json

        INPUT:
            None

        OUTPUT:
            json object with keys: measurement, tags, fields, and timestamp

        """
        # ----------------------
        # CHECK
        self.validate()

        # ----------------------
        # IF validation successful return json dict
        return {
            "measurement": self.measurement,
            "tags": self.tags,
            "fields": self.fields,
            "timestamp": self.timestamp.timestamp() if self.timestamp else None,
        }

    def from_json(
        self,
        json: dict[
            str, Union[str, dict[str, str], dict[str, Union[int, float, str]], str]
        ],
    ) -> None:
        """from_json: Set class variables

        INPUT:
            json = dictionary of line protocol

        OUTPUT:
            None, set the various class variables
                    from a json dict

        """
        measurement = json.get("measurement")
        tags = json.get("tags", {})
        fields = json.get("fields", {})
        timestamp = (
            datetime.fromtimestamp(json.get("timestamp"))
            if json.get("timestamp")
            else None
        )

        self.measurement = measurement
        self.tags = tags
        self.fields = fields
        self.timestamp = timestamp

    def parse_line_protocol(self, line_protocol: str) -> None:
        """parse_line_protocol: Set class variables from a line protocol

        INPUT:
            line_protocol = line protocol to parse

        OUTPUT:
            None, set the various class variables
                    from a line protocol

        """
        # -----------------------------------
        # Regex split on white space only that
        # are not escaped with \
        measurement_tags, fields, epoch = re.split(r"(?<!\\)\s", line_protocol)
        self.set_timestamp(datetime.fromtimestamp(convert_to_seconds(int(epoch))))

        # -----------------------------------
        # Split the measurement from the tags
        measurement, tags = re.split(r"(?<!\\),", measurement_tags, maxsplit=1)
        self.set_measurement(measurement)

        # -----------------------------------
        # For each tag split...
        tags = re.split(r"(?<!\\),", tags)

        # -----------------------------------
        # ...turn it into a dictionary
        for tag in tags:
            key, value = re.split(r"(?<!\\)=", tag)
            self.add_tag(key, value)

        # -----------------------------------
        # For each field split...
        fields = re.split(r"(?<!\\),", fields)

        # -----------------------------------
        # ...turn it into a dictionary
        for field in fields:
            key, value = re.split(r"(?<!\\)=", field)
            self.add_field(key, value)

        # -----------------------------------
        # Map field value to int or float if possible
        for k, v in self.fields.items():
            if v.isdigit():
                self.fields[k] = int(v)
            elif v.replace(".", "", 1).isdigit():
                self.fields[k] = float(v)

        # -----------------------------------
        # Convert a int timestamp to a datetime object
        # open('test.txt', 'w').write(f"{epoch} + {datetime.fromtimestamp(int(epoch))}")
        self.validate()
