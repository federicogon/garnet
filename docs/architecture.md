# Architecture

Diagrams documenting the software structure. Keep them in sync with the code
whenever the data model or the API→entity mapping changes. See
[`api-notes.md`](./api-notes.md) for the raw API payloads.

## Entity-relationship diagram (DER)

How the Garnet API objects map to Home Assistant devices and entities.

```mermaid
erDiagram
    GARNET_SYSTEM ||--o{ PARTITION : "has (estados)"
    GARNET_SYSTEM ||--|| HA_DEVICE : "becomes"
    HA_DEVICE ||--o{ HA_ALARM_PANEL : "groups"
    PARTITION ||--o| HA_ALARM_PANEL : "becomes if configured"

    GARNET_SYSTEM {
        string id PK "message.sistemas[].id (e.g. b10050019a36)"
        string nombre "system name"
        object estados "map partition -> {nombre, estado}"
    }
    PARTITION {
        string number PK "key in estados (1..4)"
        string nombre "partition name"
        string estado "disarm | arm | present | 0 (unconfigured)"
    }
    HA_DEVICE {
        tuple identifiers PK "(DOMAIN, system_id)"
        string name "system nombre"
        string manufacturer "Garnet Control"
    }
    HA_ALARM_PANEL {
        string unique_id PK "f'{system_id}_{partition}'"
        string name "partition nombre"
        enum alarm_state "DISARMED | ARMED_AWAY | ARMED_HOME"
        int supported_features "ARM_AWAY | ARM_HOME"
    }
```

Notes:

- A partition with `estado == "0"` is **unconfigured** and does **not** become an
  entity (see `PARTITION_STATE_UNCONFIGURED`).
- The `estado` maps to `DISARMED` (`"disarm"`), `ARMED_AWAY` (`"arm"`) or
  `ARMED_HOME` (`"present"` — armed with some zones bypassed).

## Sequence: populating and mapping an entity

From config-entry setup to a live `alarm_control_panel` entity, showing how the
API response is mapped into HA.

```mermaid
sequenceDiagram
    autonumber
    participant HA as Home Assistant
    participant Init as __init__.async_setup_entry
    participant Client as GarnetApiClient
    participant Coord as GarnetCoordinator
    participant Panel as alarm_control_panel
    participant API as Garnet API

    HA->>Init: async_setup_entry(entry)
    Init->>Client: GarnetApiClient(email, password, session)
    Init->>Client: async_login()
    Client->>API: POST /auth/login {email, password}
    API-->>Client: {success, accessToken}

    Init->>Coord: async_config_entry_first_refresh()
    Coord->>Client: async_get_systems()
    Client->>API: GET /systems/
    API-->>Client: message.sistemas[] (id, nombre, estados)
    Client-->>Coord: list[system]
    Note over Coord: data = {system["id"]: system}

    Init->>Panel: async_forward_entry_setups()
    Panel->>Coord: read coordinator.data
    loop for each system, each partition in estados
        alt estado == "0" (unconfigured)
            Note over Panel: skip — no entity created
        else configured
            Panel->>Panel: GarnetAlarmPanel(coordinator, system_id, partition)
        end
    end
    Panel-->>HA: async_add_entities([...])

    Note over HA,Coord: every 30s the coordinator re-polls GET /systems/
    HA->>Panel: read alarm_state
    Panel->>Coord: coordinator.data[system_id]["estados"][partition]["estado"]
    Panel->>Panel: _map_state(estado)
    Note over Panel: "disarm" -> DISARMED<br/>"arm" -> ARMED_AWAY<br/>"present" -> ARMED_HOME
    Panel-->>HA: AlarmControlPanelState
```
