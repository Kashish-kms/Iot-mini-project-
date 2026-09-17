### Mosquitto Healthcheck ACL

The broker healthcheck subscribes to the Mosquitto `$SYS/broker/uptime` topic to verify that the MQTT broker is running correctly. Therefore, the dedicated `healthcheck` user must have read-only access to this topic.

Edit the Mosquitto ACL file:

```powershell
notepad broker/acl
```

Add the following rules:

```text
user healthcheck
topic read $SYS/broker/uptime
```

The complete ACL configuration is:

```text
# =============================================================================
# Mosquitto topic ACL.
#
# Least-privilege per user. Default-deny: anything not explicitly allowed
# below is silently denied by Mosquitto.
#
# Clients / roles:
#   sim_user    = the Python sensor simulator.
#                 May only PUBLISH telemetry to the assigned room topic.
#
#   ingest_user = the MQTT-to-SQLite ingestion service.
#                 May only SUBSCRIBE to the assigned room topic.
#
#   healthcheck = broker healthcheck.
#                 May only SUBSCRIBE to the broker uptime topic.
# =============================================================================

user sim_user
topic write home/room1/telemetry

user ingest_user
topic read home/room1/telemetry

user healthcheck
topic read $SYS/broker/uptime
```

After modifying the ACL file, restart the broker so Mosquitto reloads the configuration:

```powershell
docker compose restart broker
```

This follows the project's **least-privilege** security model: each service receives access only to the MQTT topics required for its specific function.
