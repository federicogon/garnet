# Notas del API de Garnet Control

Este documento captura lo que descubramos del API que usa la aplicación web
<https://web.garnetcontrol.app/>. Se actualiza a medida que obtenemos las URLs y
respuestas reales.

> Cómo obtener esta info: abrir la web en el navegador → DevTools (F12) → pestaña
> **Network** → filtrar por `Fetch/XHR` → iniciar sesión y operar la alarma para
> ver las llamadas al API (URL, método, headers, body y respuesta).

## Base URL

- **Base del API:** `https://web.garnetcontrol.app/users_api/v1/`

## Autenticación

- **Header obligatorio en TODAS las peticiones:** **`X-Client-Web: 1`** (identifica al
  cliente web; sin él el API rechaza la petición).
- **Método:** token (`accessToken`) devuelto por el login. En las llamadas posteriores
  se envía además en el header **`x-access-token: <accessToken>`**.
- **Endpoint de login:** `POST /users_api/v1/auth/login`
  - URL completa: `https://web.garnetcontrol.app/users_api/v1/auth/login`
  - Método: `POST`
  - Body (JSON):
    ```json
    { "email": "federico.h.gon@gmail.com", "password": "password" }
    ```
  - Respuesta (JSON):
    ```json
    {
      "success": true,
      "accessToken": "token",
      "userData": { "email": "email" }
    }
    ```
- **Cómo se envía el token en llamadas posteriores:** header `x-access-token: <accessToken>`
- **Expiración / refresh:** _(por definir)_

## Endpoints

### Listar alarmas / paneles

- **URL:** `https://web.garnetcontrol.app/users_api/v1/systems/`
- **Método:** `GET`
- **Headers:** `x-access-token: <accessToken>`
- **Respuesta (ejemplo):**
  ```json
  {
    "success": true,
    "message": {
      "sistemas": [
        {
          "estados": {
            "1": { "nombre": "Sensores interior", "estado": "disarm" },
            "2": { "nombre": "Part. 2", "estado": "0" },
            "3": { "nombre": "Part. 3", "estado": "0" },
            "4": { "nombre": "Part. 4", "estado": "0" }
          },
          "partitionKeys": {
            "0": "1111",
            "1": "1111",
            "2": "2222",
            "3": "3333",
            "4": "4444"
          },
          "nombre": "Nombre Alarma",
          "id": "b10050019a36",
          "icono": 0,
          "_id": "67252e2afcc32b19a5e34042"
        }
      ],
      "sistemasCompartidos": []
    }
  }
  ```
- **Campos importantes:**
  - `message.sistemas[]` → lista de sistemas/alarmas del usuario.
  - **`message.sistemas[].id`** (p. ej. `"b10050019a36"`) → **hay que guardarlo**; es el
    identificador que se usa en las llamadas siguientes (estado, armar, desarmar).
  - `message.sistemas[].nombre` (p. ej. `"Nombre Alarma"`) → nombre del sistema.
  - `message.sistemas[]._id` → id interno de Mongo (distinto de `id`; por ahora no lo usamos).
  - `message.sistemas[].estados` → mapa de **particiones** `"1".."4"`, cada una con
    `nombre` y `estado`. Ej.: partición `"1"` = `"Sensores interior"` con estado `"disarm"`.
    Las particiones con `estado: "0"` parecen no configuradas/inactivas _(por confirmar)_.
  - `message.sistemas[].partitionKeys` → mapa `"0".."4"` con códigos PIN por partición
    (índice `0` = general). _(Uso por confirmar — probablemente requeridos para armar/desarmar.)_
  - `message.sistemasCompartidos` → sistemas compartidos con el usuario (mismo formato, vacío aquí).

> **Modelado HA (borrador):** cada partición configurada de cada sistema sería una entidad
> `alarm_control_panel`. El `unique_id` podría ser `f"{sistema.id}_{particion}"`.

### Detalle / estado de un sistema

- **URL:** `https://web.garnetcontrol.app/users_api/v1/systems/{id}/`
  (ej. `.../systems/b10050019a36/`, donde `{id}` = `message.sistemas[].id` del listado)
- **Método:** `GET`
- **Headers:** `x-access-token: <accessToken>`
- **Respuesta:** objeto grande. Estructura resumida y campos que nos interesan:

  ```jsonc
  {
    "success": true,
    "message": {
      "sistema": {                       // detalle completo del sistema
        "id": "b10050019a36",
        "nombre": "Nombre Alarma",
        "lastEventReport": "2026-07-27T01:43:38.713Z",
        "userPermissions": {
          "atributos": {                 // qué puede hacer el usuario logueado
            "puedeArmar": true,
            "puedeDesarmar": true,
            "sharedPartitions": { "0": true, "1": true, "2": true, "3": true, "4": true }
            // ... puedeInhibirZonas, puedeInteractuarConSalidas/Sirena, puedeVerCamaras
          }
        },
        "programation": {
          "data": {
            "alarmPanel": {              // modelo del panel físico
              "brand": 0, "model": 8, "modelName": "PC-860", "versionName": "1.6.0"
            },
            "partitions": [              // PARTICIONES CONFIGURADAS (las que existen de verdad)
              { "name": "Sensores interior", "number": 1, "enabled": true }
            ],
            "zones": [ /* 32 zonas: number, name, enabled, isPresentZone, ... */ ],
            "outputs": [ /* PGMs */ ],
            "automations": [ /* 20 automatizaciones */ ]
          }
        }
      },
      "sistemas": [                       // MISMO formato que el listado /systems/
        {
          "estados": {                    // <-- ESTADO ACTUAL por partición
            "1": { "nombre": "Sensores interior", "estado": "disarm" },
            "2": { "nombre": "Part. 2", "estado": "0" },
            "3": { "nombre": "Part. 3", "estado": "0" },
            "4": { "nombre": "Part. 4", "estado": "0" }
          },
          "partitionKeys": { "0": "1111", "1": "1111", "2": "2222", "3": "3333", "4": "4444" },
          "nombre": "Nombre Alarma",
          "id": "b10050019a36"
        }
      ],
      "sistemasCompartidos": []
    }
  }
  ```

- **Campos importantes:**
  - **Estado actual** → `message.sistemas[].estados["<part>"].estado`
    (para la partición 1 = `"disarm"`).
  - **Particiones reales** → `message.sistema.programation.data.partitions[]`
    (solo `number: 1` "Sensores interior" está `enabled: true`; las particiones con
    `estado: "0"` en `estados` corresponden a particiones NO configuradas → se ignoran).
  - **Permisos** → `message.sistema.userPermissions.atributos.puedeArmar` /
    `puedeDesarmar` (para saber si el usuario puede operar).
  - **Modelo del panel** → `message.sistema.programation.data.alarmPanel.modelName`
    (útil para `device_info` en HA).
  - `message.sistema.zones` / `outputs` / `automations` → fuera del alcance inicial
    (posibles `binary_sensor`/`switch` a futuro).

> **Nota:** el estado de las particiones también viene en el listado `GET /systems/`
> (campo `estados`), así que para el polling quizá alcance con ese endpoint. El detalle
> `/systems/{id}/` sirve para descubrir particiones configuradas, permisos y el modelo.

### Última actualización del sistema

- **URL:** `https://web.garnetcontrol.app/users_api/v1/systems/{id}/lastUpdate`
  (ej. `.../systems/b10050019a36/lastUpdate`)
- **Método:** `GET`
- **Headers:** `x-access-token: <accessToken>`
- **Respuesta (ejemplo):**
  ```json
  {
    "success": true,
    "message": {
      "lastUpdate": "2025-10-30T09:33:49.338Z",
      "lastEvent": "2025-10-29T21:37:16.208Z"
    }
  }
  ```
- **Campos:**
  - `message.lastUpdate` → última vez que se actualizó la config/estado del sistema.
  - `message.lastEvent` → último evento de la alarma.
- **Uso posible en HA:** endpoint liviano para el polling. Se podría consultar primero
  `lastUpdate` y solo pedir el detalle completo cuando cambie (evita traer el objeto grande
  en cada refresco). _(Por confirmar si `lastUpdate` cambia al armar/desarmar.)_

### Listar eventos

- **URL:** `https://web.garnetcontrol.app/users_api/v1/systems/{id}/commands/newevents`
  (ej. `.../systems/b10050019a36/commands/newevents`)
- **Método:** `POST`
- **Headers:** `x-access-token: <accessToken>`
- **Body / filtro:** _(por definir)_
- **Respuesta (ejemplo):**
  ```jsonc
  {
    "success": true,
    "message": {
      "response": {
        "eventosArray": [
          {
            "code": 14,
            "seq": "065",
            "particion": 0,
            "date": "2026-06-10T13:27:23.000Z",
            "qualifier": 1,
            "zonaUsuario": 0,
            "eventGroup": 3,
            "eventText": "Falla de energía eléctrica",
            "_id": "6a296cec57af26592236ffa3"
          }
          // ... más eventos
        ]
      }
    }
  }
  ```
- **Campos por evento** (`message.response.eventosArray[]`):
  - `code` → código numérico del evento.
  - `eventText` → descripción legible (ej. `"Falla de energía eléctrica"`).
  - `eventGroup` → grupo/categoría del evento _(valores por definir)_.
  - `date` → fecha/hora ISO del evento.
  - `particion` → partición afectada (`0` = general/sistema).
  - `zonaUsuario` → zona o usuario asociado _(por confirmar semántica)_.
  - `qualifier` → calificador _(por definir — ¿1 = nuevo/activo, 3 = restauración?)_.
  - `seq` → número de secuencia del evento.
  - `_id` → id interno de Mongo.
- **Uso posible en HA:** exponer los últimos eventos (p. ej. un sensor de "último evento"
  con `eventText`/`date`, atributos con el historial, o disparadores para automatizaciones).

### Obtener el `timeout` para comandos

- **URL:** `https://web.garnetcontrol.app/users_api/v1/systems/{id}/timeout`
  (ej. `.../systems/b10050019a36/timeout`)
- **Método:** `GET` _(por confirmar)_
- **Headers:** `x-access-token: <accessToken>`
- **Respuesta (ejemplo):**
  ```json
  { "success": true, "message": { "timeout": 8500 } }
  ```
- **Uso:** el valor `message.timeout` es el que hay que enviar en el body (`timeout`) de los
  comandos de **armar** (`arm/away`, `arm/delayed`) y **desarmar** (`disarm`).
  → Flujo: llamar a este endpoint justo antes de enviar un comando y usar el `timeout` devuelto.

### Armar la alarma — "Ausente" (armed_away)

- **URL:** `https://web.garnetcontrol.app/users_api/v1/systems/{id}/commands/arm/away`
  (ej. `.../systems/b10050019a36/commands/arm/away`)
- **Método:** `POST`
- **Headers:** `x-access-token: <accessToken>`
- **Body (JSON):**
  ```json
  { "seq": "002", "partNumber": "1", "timeout": 8500 }
  ```
  - `seq` → número de secuencia del comando (string, padding a 3 dígitos: `"001"`).
    Lo maneja **el cliente** (no el servidor) y es **por sesión**: empieza en `001` y se
    incrementa +1 por cada comando enviado a la alarma (armar/desarmar). Al llegar a `999`
    vuelve a `001` (en la práctica nunca se llega). → En la integración: contador en memoria
    por sesión (reinicia a `001` en cada login/arranque), sin necesidad de persistirlo.
  - `partNumber` → número de partición a armar (string), ej. `"1"`.
  - `timeout` → tiempo de espera del comando en ms (ej. `8500`). Se obtiene del endpoint
    `GET /systems/{id}/timeout` (ver arriba), llamándolo antes de cada comando.
- **Respuesta (ejemplo):**
  ```json
  {
    "success": true,
    "message": {
      "response": "COMANDO ENVIADO CON EXITO",
      "status": "100007800000000000000000000000000000000"
    }
  }
  ```
  - `message.response` → confirmación textual del envío del comando.
  - `message.status` → string de estado (bitmap/hex del panel). _(Por decodificar; parece
    codificar el estado resultante de las particiones.)_

> **Nota:** la respuesta confirma el **envío** del comando, no necesariamente el estado
> final. Probablemente haya que re-consultar el estado (`/systems/{id}/` → `estados`) tras
> un pequeño retardo para reflejar `armed_away` en HA.

### Armar la alarma — "Presente" (armed_home)

- **URL:** `https://web.garnetcontrol.app/users_api/v1/systems/{id}/commands/arm/delayed`
  (ej. `.../systems/b10050019a36/commands/arm/delayed`)
- **Método:** `POST`
- **Headers:** `x-access-token: <accessToken>`
- **Body (JSON):** igual que "Ausente" → `{ "seq": "002", "partNumber": "1", "timeout": 8500 }`
- **Respuesta:** igual formato → `{ success, message: { response, status } }`
- **Nota:** el path es `arm/delayed` (armado "Presente"/con demora), a diferencia de
  `arm/away` (armado "Ausente").

### Desarmar la alarma

- **URL:** `https://web.garnetcontrol.app/users_api/v1/systems/{id}/commands/disarm`
  (ej. `.../systems/b10050019a36/commands/disarm`)
- **Método:** `POST`
- **Headers:** `x-access-token: <accessToken>`
- **Body (JSON):** igual que armar → `{ "seq": "002", "partNumber": "1", "timeout": 8500 }`
- **Respuesta:** igual formato que armar → `{ success, message: { response, status } }`

## Mapeo de estados

Correspondencia entre los estados del API de Garnet y los estados de Home Assistant
(`AlarmControlPanelState`):

| Estado Garnet (API)          | Estado Home Assistant |
| ---------------------------- | --------------------- |
| `"disarm"`                   | `disarmed`            |
| `"arm"`                      | `armed_away`          |
| `"present"`                  | `armed_home`          |
| `"triggered"`                | `triggered`           |
| `"0"` (partición no config.) | _(no crear entidad)_  |

> `"arm"` = armada "Ausente" (`arm/away`). `"present"` = armada "Presente" (`arm/delayed`):
> armada pero con algunas zonas/sensores desactivados → se mapea a `armed_home`.
> `"triggered"` = **alarma sonando** (sirena activada) → se mapea a `triggered`.
> `"disarm"` = desarmada; `"0"` = partición no configurada.

## Preguntas abiertas

- ✅ **¿Existen particiones o zonas?** Sí. Particiones (hasta 4, definidas en
  `programation.data.partitions`) y zonas (hasta 32). El alcance inicial son las particiones.
- ¿Un usuario puede tener más de una alarma/panel? (el array `sistemas` lo permite; en el
  ejemplo hay solo una).
- ✅ ¿Qué valores de `estado` devuelve el API cuando la alarma está **armada** o
  **sonando**? `"arm"` (ausente), `"present"` (presente) y `"triggered"` (sonando).
- ¿El armado/desarmado requiere el PIN de `partitionKeys` en el body, o basta la sesión?
- ¿Hay rate limiting? ¿Cada cuánto se puede consultar el estado (polling)?
- ¿Existe algún endpoint/push para estado en tiempo real, o solo polling?
