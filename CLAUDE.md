# Garnet Control — Home Assistant integration

Custom integration (HACS) that controls Garnet Control alarms through the
`web.garnetcontrol.app` API, exposing each partition as an `alarm_control_panel`
entity.

## Code guidelines

- **Language of the code: English.** All variable names, function names,
  comments, and docstrings must be written in English.
- **User-facing language: English + Spanish.** The application must support both
  languages. Any string shown to the user must be localizable, not hardcoded:
  keep translations in `custom_components/garnet_control/translations/en.json` and
  `es.json`, and never embed user-facing text directly in the Python code.
- **User-facing strings and errors live in `strings.json`.** Every string or
  error message shown to the user must be defined in
  `custom_components/garnet_control/strings.json` (the English base) and referenced by
  key from the code — never hardcode user-facing text in Python. Keep
  `translations/en.json` and `translations/es.json` in sync with it. Internal
  exception messages and log lines are code (English), not user-facing strings.
- **Document the structure with Mermaid diagrams when relevant.** Keep the
  diagrams in [`docs/architecture.md`](docs/architecture.md) and update them
  whenever the relevant code changes. At minimum, always maintain:
  - an **ER diagram (DER)** of the data model, and
  - a **sequence diagram** of how an entity is populated and mapped from the
    Garnet API into the Home Assistant entity.
