"""Constants for the Garnet Control integration."""

from __future__ import annotations

DOMAIN = "garnet_control"

# Base of the API used by the web app https://web.garnetcontrol.app/
API_BASE = "https://web.garnetcontrol.app/users_api/v1"

# Authentication header used on calls after login.
AUTH_HEADER = "x-access-token"

# Header required by the API on EVERY request (identifies the web client).
CLIENT_HEADER = "X-Client-Web"
CLIENT_HEADER_VALUE = "1"

# State polling interval (seconds).
DEFAULT_SCAN_INTERVAL = 30

# Default timeout for HTTP requests (seconds).
REQUEST_TIMEOUT = 15

# Arm/disarm command paths (relative to /systems/{id}/commands/).
CMD_ARM_AWAY = "arm/away"      # "Away" -> armed_away
CMD_ARM_HOME = "arm/delayed"   # "Home" -> armed_home
CMD_DISARM = "disarm"

# `estado` value of an UNCONFIGURED partition (skipped, no entity is created).
PARTITION_STATE_UNCONFIGURED = "0"

# Known `estado` values of a partition.
PARTITION_STATE_DISARMED = "disarm"
PARTITION_STATE_ARMED = "arm"          # "Away" -> armed_away
PARTITION_STATE_PRESENT = "present"    # "Home" -> armed_home (armed with some zones bypassed)
