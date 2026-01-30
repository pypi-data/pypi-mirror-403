# juniconnlib

This python library serves as core library (hence the name `juniconnlib_core`)
towards connecting all different kinds of components to a FIWARE based
infrastructure. For an overview of related projects, that are build on top
of `juniconnlib_core`, take a look at [related projects](#related-projects).

The library is built ontop of the framework
[`AgentLib`](https://github.com/RWTH-EBC/AgentLib) developed by the EBC
and RWTH Aachen and extends the functionality for interacting with the
FIWARE platform components. The main components allow for:

* Device provisioning at the IoT-Agent (JSON)
* Entity provisioning at the Orion Context Broker
* Sending and receiving messages from the IoT-Agent (JSON) using MQTT
* Posting subscriptions to the Orion Context Broker
* Sending (HTTP) and receiving data (from subscriptions with MQTT notification)
  from the Orion Context Broker
* Working around JSON-Schema data models and creating devices and context
  entities from these

It contains various modules for device provisioning to FIWARE and data transfer
between field devices and FIWARE.

## Related Projects

**juniconnlib\_core** serves as a base library for a multitude of other
libraries. Most of the other projects work around the integration of different
protocols and physical devices into the FIWARE architecture. Bundling
everything that is necessary to communicate with FIWARE felt like a natural
step, so related projects just need to implement use case specific functionality.

Notable related projects are:

* OPC UA Agent: A generalized protocol Adapter between OPC UA and FIWARE NGSIv2
* LoRaWAN Agent: A generalized protocol Adapter between LoRaWAN and FIWARE NGSIv2
* Messdas Agent: A protocol adapter, that integrates data from the commercial
  MESSDAS software into FIWARE NGSIv2
* And multiple other protocol converters (e.g. integration of different MODBUS
  devices into the FIWARE platform)
* [FiLiP](https://github.com/RWTH-EBC/FiLiP): A python API wrapper based on pydantic
  and requests for easy data validation a interaction with the FIWARE components
* [FiDERe](https://jugit.fz-juelich.de/iek-10/public/ict-platform/fiware-applications/fidere):
  A library for parsing JSON schema data models that represent entities in
  NGSIv2 normalized format, validating data and creating FiLiP compatible
  `ContextEntity` and `Device` objects.

## Documentation

Documentation is available at
https://apps.fz-juelich.de/ice-1/ict-platform/juniconnlib-core and is
up-to-date with the most recent release. Building and publishing of the
documentation is done via CI/CD upon tag creation and commits to the `master` 
branch.

In addition, you can find a complete demonstration of the intended usage of
**juniconnlib\_core**
[here](https://jugit.fz-juelich.de/iek-10/core-projects/llec/juniconnlib/example-agent)

## Installation

Clone the repository and into main directory and install
juniconnlib as package using pip:

```sh
pip install .
```

## Tests

Testing is done automatically on commit using CI/CD, including integration
tests for most things. A dedicated FIWARE cluster is instantiated inside the
pipeline for that.

If you want to run tests locally install the optional dependencies

```shell
pip install .[test]
```

and make sure the `ENV` variables are set correctly. You can find an example
in `./tests/.env_example`. Finally, run using pytest

```shell
pytest test_*.py
```

A bit more special is Keycloak. The FIWARE cluster running during each
pipeline does not include a Keycloak for authentication (as it takes too
long to start up). Yet still integration tests for Keycloak are available,
besides the obvious mocked ones.
The integration tests for Keycloak are marked with `keycloakintegrationtest`
and if you don't have keycloak credentials or are not using authentication
at all you can skip these tests by just executing `pytest` without the
marker:

```sh
pytest -m "not keycloakintegrationtest"
```

As an alternative if you don't set a value for the environment variable
`KEYCLOAK_URL` the integration tests are skipped by default.
Below you can see an overview of the environment variables used for all the
integration test.

| Name                        | Default Value                                        | Description                                                                     |
|-----------------------------|------------------------------------------------------|---------------------------------------------------------------------------------|
| `OCB_NOAUTH_URL`            | `http://orion:1026`                                  | Orion Context Broker (unauthenticated) URL                                      |
| `OCB_AUTH_URL`              | `http://orion:1026`                                  | Orion Context Broker (authenticated) URL                                        |
| `IOTA_NOAUTH_URL`           | `http://iot-agent-json:4041`                         | IoT Agent (unauthenticated) URL                                                 |
| `IOTA_AUTH_URL`             | `http://iot-agent-json:4041`                         | IoT Agent (authenticated) URL                                                   |
| `NOAUTH_FIWARE_SERVICE`     | `test_service`                                       | FIWARE service header for unauthenticated requests                              |
| `NOAUTH_FIWARE_SERVICEPATH` | `/`                                                  | FIWARE service path for unauthenticated requests                                |
| `AUTH_FIWARE_SERVICE`       | `test_auth_service`                                  | FIWARE service header for authenticated requests                                |
| `AUTH_FIWARE_SERVICEPATH`   | `/`                                                  | FIWARE service path for authenticated requests                                  |
| `KEYCLOAK_URL`              | `None`                                               | Keycloak server URL, if not defined `keycloakintegrationtest`s are skipped      |
| `KEYCLOAK_CREDENTIALS_FILE` | `<repo-root>/configs/keycloak_credentials_file.json` | Path to Keycloak credentials JSON file (must contain "username" and "password") |
| `OCB_CLIENT_ID`             | `orion`                                              | Keycloak client ID for Orion Context Broker                                     |
| `IOTA_CLIENT_ID`            | `iot-agent`                                          | Keycloak client ID for IoT Agent                                                |

An example for how the content of the Keycloak credentials file should look
is found in `./tests/config/keycloak_credentials_file.json`.

## Contributing

Contributing to **juniconnlib_core**, and its related projects is highly
appreciated. Contributions can take all kinds of forms, but in general
everything should be done via this Repository or by contacting
[ice-1-fiware-admin@fz-juelich.de](mailto:ice-1-fiware-admin@fz-juelich.de?subject=Possible%20Contribution%20to%20Juniconnlib-Core).
If you are interested in using **juniconnlib_core** or its related project,
feel free to reach out. In case of bugs or problems, don't be shy on raising
issues or asking questions.
