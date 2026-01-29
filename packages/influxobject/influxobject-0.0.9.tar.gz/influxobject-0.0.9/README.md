# Influx Point

## Description

This module enables the creation of an influx point object that can be transformed into either a JSON or LineProtocol format.

### Features

#### InfluxDB Line Protocol Format

The InfluxDB Line Protocol is a text-based format designed for the efficient writing of time-series data into InfluxDB. It organizes the data points with timestamps, measurement names, fields (key-value pairs representing the data), and tags (optional key-value pairs used to store metadata that describes the data). The format is highly optimized for time-series data, enabling quick parsing and writing. A typical line in this format looks like this:

> measurementName,tagKey=tagValue fieldKey="fieldValue" 1465839830100400200

- measurementName: Identifies the measurement.
- tagKey=tagValue: Zero or more tag sets separated by commas. Tags are optional but recommended for indexing.
- fieldKey="fieldValue": At least one field set, with multiple fields separated by commas. Fields are the actual data points.
- 1465839830100400200: An optional timestamp for the data point. If not specified, the server's current time is used.

### JSON Format

The JSON format offers a more flexible way to represent data. 

```json
{
    "measurement": "measurement",
    "tags": {"tag1": "value1"},
    "fields": {"field1": 1, "field2": 2},
    "timestamp": 1609455600,
}
```

## Usage

```python

    from influxobject.influxpoint import InfluxPoint

    influx_point = InfluxPoint()
    influx_point.set_measurement("measurement")
    influx_point.set_tags({"tag1": "value1"})
    influx_point.set_fields({"field1": 1, "field2": 2})
    influx_point.set_timestamp(datetime.datetime(2021, 1, 1))\
    
    print(influx_point.to_json())

        # {
        #     "measurement": "measurement",
        #     "tags": {"tag1": "value1"},
        #     "fields": {"field1": 1, "field2": 2},
        #     "timestamp": 1609455600,
        # }
        
    print(influx_point.to_line_protocol())

        # "measurement,tag1=value1 field1=1,field2=2 1609455600"
```

All functinoalities of the InfluxPoint object are listed below:

```python
    import influxobject
    x = influxobject.InfluxPoint()
    x.
        x.add_field(..., ...)
        x.from_json(...)
        x.remove_field(...)
        x.set_measurement(...)
        x.to_line_protocol()
        x.add_tag(..., ...)
        x.remove_tag(...)
        x.set_tags(...)
        x.validate()
        x.parse_line_protocol(...)
        x.set_fields(...)
        x.set_timestamp(...)
        x.to_json()
```

## Installation

To install the package use the pip package manager

```bash
    pip install influxobject
```

## Development

Tox is used as the test runner for this project. To run the entire tox suite use the following command:

```bash
    tox
```

To only run the tests under python 3.9

```bash
    tox -e py39
```

Build

```bash
    python setup.py sdist
```

Publish

```bash
    twine upload dist/*
```
