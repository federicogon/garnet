# Garnet Control – Integración para Home Assistant (NO OFICIAL)

Integración personalizada (custom integration) para [Home Assistant](https://www.home-assistant.io/)
que permite controlar sistemas de alarma **Garnet Control** a través del API que utiliza la
aplicación web <https://web.garnetcontrol.app/>.


> ⚠️ **Estado:** en desarrollo. El API todavía se está documentando mediante ingeniería
> inversa de la aplicación web. Ver [`docs/api-notes.md`](docs/api-notes.md).

## Funcionalidad objetivo

La integración expondrá cada alarma como una entidad
[`alarm_control_panel`](https://www.home-assistant.io/integrations/alarm_control_panel/) que permite:

- 🔎 **Ver el estado** de la alarma (armada / desarmada / etc.).
- 🔴 **Armar** la alarma.
- 🟢 **Desarmar** la alarma.

## Requerimientos

### Del usuario final

- Home Assistant `2026.5.3` o superior.
- Una cuenta válida en <https://web.garnetcontrol.app/> (usuario / contraseña).
- Conectividad de red hacia el API de Garnet Control desde el host de Home Assistant.

### Para publicar en HACS

Requisitos según la [documentación de HACS](https://www.hacs.xyz/docs/publish/integration/):

- Una sola integración por repositorio (un único subdirectorio en `custom_components/`).
- Repositorio público en GitHub con releases (recomendado).
- Estructura de archivos (ver más abajo).
- `manifest.json` con los campos: `domain`, `name`, `version`, `documentation`,
  `issue_tracker`, `codeowners`.
- `hacs.json` en la raíz del repositorio.
- Directorio `brand/` con al menos un `icon.png`.

## Estructura del repositorio (objetivo)

```
garnet/
├── custom_components/
│   └── garnet/
│       ├── __init__.py            # Setup de la integración + coordinator
│       ├── manifest.json          # Metadatos requeridos por HA / HACS
│       ├── config_flow.py         # Configuración vía UI (usuario/contraseña)
│       ├── const.py               # Constantes (DOMAIN, endpoints, etc.)
│       ├── coordinator.py         # DataUpdateCoordinator (polling del estado)
│       ├── api.py                 # Cliente del API de Garnet Control
│       ├── alarm_control_panel.py # Entidad de alarma (estado + armar/desarmar)
│       └── strings.json           # Textos de la UI
├── brand/
│   └── icon.png                   # Requerido por HACS
├── hacs.json                      # Configuración de HACS
├── docs/
│   └── api-notes.md               # Notas de ingeniería inversa del API
└── README.md
```

## Documentación del proyecto

- [`docs/api-notes.md`](docs/api-notes.md) — endpoints del API, autenticación, payloads
  y mapeo de estados. **Se irá completando** conforme descubramos el API.

## Instalación (HACS) — pendiente

Se documentará una vez publicado el repositorio.

## Licencia

Por definir.
