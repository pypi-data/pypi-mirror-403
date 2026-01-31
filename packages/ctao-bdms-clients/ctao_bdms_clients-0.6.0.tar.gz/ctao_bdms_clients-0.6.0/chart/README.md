# bdms

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: dev](https://img.shields.io/badge/AppVersion-dev-informational?style=flat-square)

A Helm chart for the bdms project

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| The BDMS Authors |  |  |

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://rucio.github.io/helm-charts | rucio-daemons | 39.0.0 |
| https://rucio.github.io/helm-charts | rucio-server | 39.0.0 |
| oci://harbor.cta-observatory.org/common | cert-generator-grid | v4.0.0 |
| oci://harbor.cta-observatory.org/dpps | iam(dpps-iam) | v0.1.2 |
| oci://harbor.cta-observatory.org/dpps | fts | v0.3.2 |
| oci://harbor.cta-observatory.org/proxy_cache/bitnamicharts | postgresql | 15.5.38 |
| oci://harbor.cta-observatory.org/proxy_cache/bitnamicharts | redis | 22.0.7 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| _protocols_common.domains.lan.delete | int | `1` |  |
| _protocols_common.domains.lan.read | int | `1` |  |
| _protocols_common.domains.lan.write | int | `1` |  |
| _protocols_common.domains.wan.delete | int | `1` |  |
| _protocols_common.domains.wan.read | int | `1` |  |
| _protocols_common.domains.wan.third_party_copy_read | int | `1` |  |
| _protocols_common.domains.wan.third_party_copy_write | int | `1` |  |
| _protocols_common.domains.wan.write | int | `1` |  |
| _protocols_common.extended_attributes | string | `"None"` |  |
| _protocols_common.impl | string | `"rucio.rse.protocols.gfal.Default"` |  |
| _protocols_common.port | int | `1094` |  |
| _protocols_common.prefix | string | `"//rucio"` |  |
| acada_ingest.daemon.config.celery_broker_url | string | `"redis://bdms-redis-master:6379/0"` |  |
| acada_ingest.daemon.config.celery_result_backend | string | `"redis://bdms-redis-master:6379/1"` |  |
| acada_ingest.daemon.config.data_path | string | `"/storage-1/"` |  |
| acada_ingest.daemon.config.disable_metrics | bool | `false` |  |
| acada_ingest.daemon.config.lock_file | string | `"/storage-1/bdms_ingest.lock"` |  |
| acada_ingest.daemon.config.log_file | string | `nil` | The path to the log file, if not specified, logs to stdout |
| acada_ingest.daemon.config.log_level | string | `"DEBUG"` | The logging level for the ingestion daemon |
| acada_ingest.daemon.config.metrics_port | int | `8000` | The port for the Prometheus metrics server |
| acada_ingest.daemon.config.offsite_copies | int | `2` |  |
| acada_ingest.daemon.config.polling_interval | float | `1` |  |
| acada_ingest.daemon.config.rse | string | `"STORAGE-1"` |  |
| acada_ingest.daemon.config.scope | string | `"test_scope_persistent"` |  |
| acada_ingest.daemon.config.task_max_retries | int | `10` | celery task retry config |
| acada_ingest.daemon.config.task_retry_backoff | bool | `true` |  |
| acada_ingest.daemon.config.task_retry_backoff_max | int | `600` |  |
| acada_ingest.daemon.config.task_retry_jitter | bool | `true` |  |
| acada_ingest.daemon.config.vo | string | `"ctao.dpps.test"` |  |
| acada_ingest.daemon.replicas | int | `0` | The number of replicas of the ingestion daemon to run, set to 0 to disable the daemon |
| acada_ingest.daemon.service.enabled | bool | `true` |  |
| acada_ingest.daemon.service.type | string | `"ClusterIP"` |  |
| acada_ingest.image.repository | string | `"harbor.cta-observatory.org/dpps/bdms-client"` | The container image repository for the ingestion daemon |
| acada_ingest.image.tag | string | `nil` | The specific image tag to use for the ingestion daemon |
| acada_ingest.securityContext.fsGroup | int | `0` |  |
| acada_ingest.securityContext.runAsGroup | int | `0` |  |
| acada_ingest.securityContext.runAsUser | int | `0` | The security context for the ingestion daemon, it defines the user and group IDs under which the container runs |
| acada_ingest.securityContext.supplementalGroups | list | `[]` |  |
| acada_ingest.volumeMounts[0].mountPath | string | `"/storage-1/"` |  |
| acada_ingest.volumeMounts[0].name | string | `"storage-1-data"` |  |
| acada_ingest.volumeMounts[1].mountPath | string | `"/etc/grid-security/ca.pem"` |  |
| acada_ingest.volumeMounts[1].name | string | `"cafile"` |  |
| acada_ingest.volumeMounts[1].subPath | string | `"ca.pem"` |  |
| acada_ingest.volumeMounts[2].mountPath | string | `"/etc/grid-security/certificates/74df993b.0"` |  |
| acada_ingest.volumeMounts[2].name | string | `"cafile"` |  |
| acada_ingest.volumeMounts[2].subPath | string | `"ca.pem"` |  |
| acada_ingest.volumeMounts[3].mountPath | string | `"/etc/grid-security/certificates/74df993b.r0"` |  |
| acada_ingest.volumeMounts[3].name | string | `"cafile"` |  |
| acada_ingest.volumeMounts[3].subPath | string | `"dpps_test_ca.crl.r0"` |  |
| acada_ingest.volumeMounts[4].mountPath | string | `"/opt/rucio/etc/usercert.pem"` |  |
| acada_ingest.volumeMounts[4].name | string | `"dppsuser-cert"` |  |
| acada_ingest.volumeMounts[4].subPath | string | `"dppsuser.pem"` |  |
| acada_ingest.volumeMounts[5].mountPath | string | `"/opt/rucio/etc/userkey.pem"` |  |
| acada_ingest.volumeMounts[5].name | string | `"dppsuser-key"` |  |
| acada_ingest.volumeMounts[5].subPath | string | `"dppsuser.key.pem"` |  |
| acada_ingest.volumes[0].name | string | `"storage-1-data"` |  |
| acada_ingest.volumes[0].persistentVolumeClaim.claimName | string | `"storage-1-pvc"` |  |
| acada_ingest.volumes[1].name | string | `"cafile"` |  |
| acada_ingest.volumes[1].secret.defaultMode | int | `420` |  |
| acada_ingest.volumes[1].secret.secretName | string | `"bdms-server-cafile"` |  |
| acada_ingest.volumes[2].name | string | `"dppsuser-cert"` |  |
| acada_ingest.volumes[2].secret.defaultMode | int | `420` |  |
| acada_ingest.volumes[2].secret.secretName | string | `"bdms-dppsuser-certkey"` |  |
| acada_ingest.volumes[3].name | string | `"dppsuser-key"` |  |
| acada_ingest.volumes[3].secret.defaultMode | int | `256` |  |
| acada_ingest.volumes[3].secret.secretName | string | `"bdms-dppsuser-certkey"` |  |
| acada_ingest.workers.autoscaling.max_replicas | int | `10` |  |
| acada_ingest.workers.autoscaling.min_replicas | int | `1` |  |
| acada_ingest.workers.autoscaling.target_cpu | int | `70` |  |
| acada_ingest.workers.autoscaling.target_memory | int | `80` |  |
| acada_ingest.workers.concurrency | int | `4` |  |
| acada_ingest.workers.enabled | bool | `true` |  |
| acada_ingest.workers.max_tasks_per_child | int | `20` |  |
| acada_ingest.workers.replicas | int | `2` |  |
| acada_ingest.workers.resources.limits.cpu | string | `"2000m"` |  |
| acada_ingest.workers.resources.limits.memory | string | `"4Gi"` |  |
| acada_ingest.workers.resources.limits.storage | string | `"3Gi"` |  |
| acada_ingest.workers.resources.requests.cpu | string | `"500m"` |  |
| acada_ingest.workers.resources.requests.memory | string | `"1Gi"` |  |
| acada_ingest.workers.resources.requests.storage | string | `"1Gi"` |  |
| bootstrap.image.repository | string | `"harbor.cta-observatory.org/dpps/bdms-rucio-server"` | The container image for bootstrapping Rucio (initialization, configuration) with the CTAO Rucio policy package installed |
| bootstrap.image.tag | string | `"39.0.0-v0.5.0"` | The specific image tag to use for the bootstrap container |
| bootstrap.pg_image.repository | string | `"harbor.cta-observatory.org/proxy_cache/postgres"` | Postgres client image used to wait for db readines during bootstrap |
| bootstrap.pg_image.tag | string | `"16.3-bookworm"` | Postgres client image tag used to wait for db readines during bootstrap |
| cert-generator-grid.enabled | bool | `true` |  |
| cert-generator-grid.extra_server_names[0] | string | `"iam.test.example"` |  |
| cert-generator-grid.extra_server_names[1] | string | `"voms.test.example"` |  |
| cert-generator-grid.extra_server_names[2] | string | `"rucio-storage-1"` |  |
| cert-generator-grid.extra_server_names[3] | string | `"rucio-storage-2"` |  |
| cert-generator-grid.extra_server_names[4] | string | `"rucio-storage-3"` |  |
| cert-generator-grid.extra_server_names[5] | string | `"fts"` |  |
| cert-generator-grid.generatePreHooks | bool | `true` |  |
| cert-generator-grid.users[0].name | string | `"DPPS User"` |  |
| cert-generator-grid.users[0].suffix | string | `""` |  |
| cert-generator-grid.users[1].name | string | `"DPPS User Unprivileged"` |  |
| cert-generator-grid.users[1].suffix | string | `"-unprivileged"` |  |
| cert-generator-grid.users[2].name | string | `"Non-DPPS User"` |  |
| cert-generator-grid.users[2].suffix | string | `"-non-dpps"` |  |
| cert-generator-grid.users[3].name | string | `"Non-CTAO User"` |  |
| cert-generator-grid.users[3].suffix | string | `"-non-ctao"` |  |
| configure.as_hook | bool | `false` |  |
| configure.extra_script | string | `"# add a scope\nrucio scope add --account root root || echo \"Scope 'root' already exists\"\nrucio did add --type container /ctao.dpps.test || echo \"Container /ctao.dpps.test already exists\"\n"` | This script is executed after the Rucio server is deployed and configured. It can be used to perform additional configuration or setup tasks if they currently cannot be done with the chart values. |
| configure.identities[0].account | string | `"root"` |  |
| configure.identities[0].email | string | `"dpps-test@cta-observatory.org"` |  |
| configure.identities[0].id | string | `"CN=DPPS User"` |  |
| configure.identities[0].type | string | `"X509"` |  |
| configure.rse_distances | list | `[["STORAGE-1","STORAGE-2",1],["STORAGE-2","STORAGE-1",1],["STORAGE-1","STORAGE-3",1],["STORAGE-3","STORAGE-1",1],["STORAGE-2","STORAGE-3",1],["STORAGE-3","STORAGE-2",1]]` | A list of RSE distance specifications, each a list of 3 values: source RSE, destination RSE and distance (integer) |
| configure.rses.STORAGE-1.attributes.ANY | bool | `true` |  |
| configure.rses.STORAGE-1.attributes.ONSITE | bool | `true` |  |
| configure.rses.STORAGE-1.attributes.fts | string | `"https://bdms-fts:8446"` |  |
| configure.rses.STORAGE-1.limits_by_account.root | string | `"infinity"` |  |
| configure.rses.STORAGE-1.protocols[0].<<.domains.lan.delete | int | `1` |  |
| configure.rses.STORAGE-1.protocols[0].<<.domains.lan.read | int | `1` |  |
| configure.rses.STORAGE-1.protocols[0].<<.domains.lan.write | int | `1` |  |
| configure.rses.STORAGE-1.protocols[0].<<.domains.wan.delete | int | `1` |  |
| configure.rses.STORAGE-1.protocols[0].<<.domains.wan.read | int | `1` |  |
| configure.rses.STORAGE-1.protocols[0].<<.domains.wan.third_party_copy_read | int | `1` |  |
| configure.rses.STORAGE-1.protocols[0].<<.domains.wan.third_party_copy_write | int | `1` |  |
| configure.rses.STORAGE-1.protocols[0].<<.domains.wan.write | int | `1` |  |
| configure.rses.STORAGE-1.protocols[0].<<.extended_attributes | string | `"None"` |  |
| configure.rses.STORAGE-1.protocols[0].<<.impl | string | `"rucio.rse.protocols.gfal.Default"` |  |
| configure.rses.STORAGE-1.protocols[0].<<.port | int | `1094` |  |
| configure.rses.STORAGE-1.protocols[0].<<.prefix | string | `"//rucio"` |  |
| configure.rses.STORAGE-1.protocols[0].hostname | string | `"rucio-storage-1"` |  |
| configure.rses.STORAGE-1.protocols[0].scheme | string | `"davs"` |  |
| configure.rses.STORAGE-1.rse_type | string | `"DISK"` |  |
| configure.rses.STORAGE-2.attributes.ANY | bool | `true` |  |
| configure.rses.STORAGE-2.attributes.OFFSITE | bool | `true` |  |
| configure.rses.STORAGE-2.attributes.fts | string | `"https://bdms-fts:8446"` |  |
| configure.rses.STORAGE-2.limits_by_account.root | int | `-1` |  |
| configure.rses.STORAGE-2.protocols[0].<<.domains.lan.delete | int | `1` |  |
| configure.rses.STORAGE-2.protocols[0].<<.domains.lan.read | int | `1` |  |
| configure.rses.STORAGE-2.protocols[0].<<.domains.lan.write | int | `1` |  |
| configure.rses.STORAGE-2.protocols[0].<<.domains.wan.delete | int | `1` |  |
| configure.rses.STORAGE-2.protocols[0].<<.domains.wan.read | int | `1` |  |
| configure.rses.STORAGE-2.protocols[0].<<.domains.wan.third_party_copy_read | int | `1` |  |
| configure.rses.STORAGE-2.protocols[0].<<.domains.wan.third_party_copy_write | int | `1` |  |
| configure.rses.STORAGE-2.protocols[0].<<.domains.wan.write | int | `1` |  |
| configure.rses.STORAGE-2.protocols[0].<<.extended_attributes | string | `"None"` |  |
| configure.rses.STORAGE-2.protocols[0].<<.impl | string | `"rucio.rse.protocols.gfal.Default"` |  |
| configure.rses.STORAGE-2.protocols[0].<<.port | int | `1094` |  |
| configure.rses.STORAGE-2.protocols[0].<<.prefix | string | `"//rucio"` |  |
| configure.rses.STORAGE-2.protocols[0].hostname | string | `"rucio-storage-2"` |  |
| configure.rses.STORAGE-2.protocols[0].scheme | string | `"davs"` |  |
| configure.rses.STORAGE-2.recreate_if_exists | bool | `true` |  |
| configure.rses.STORAGE-3.attributes.ANY | bool | `true` |  |
| configure.rses.STORAGE-3.attributes.OFFSITE | bool | `true` |  |
| configure.rses.STORAGE-3.attributes.fts | string | `"https://bdms-fts:8446"` |  |
| configure.rses.STORAGE-3.limits_by_account.root | int | `-1` |  |
| configure.rses.STORAGE-3.protocols[0].<<.domains.lan.delete | int | `1` |  |
| configure.rses.STORAGE-3.protocols[0].<<.domains.lan.read | int | `1` |  |
| configure.rses.STORAGE-3.protocols[0].<<.domains.lan.write | int | `1` |  |
| configure.rses.STORAGE-3.protocols[0].<<.domains.wan.delete | int | `1` |  |
| configure.rses.STORAGE-3.protocols[0].<<.domains.wan.read | int | `1` |  |
| configure.rses.STORAGE-3.protocols[0].<<.domains.wan.third_party_copy_read | int | `1` |  |
| configure.rses.STORAGE-3.protocols[0].<<.domains.wan.third_party_copy_write | int | `1` |  |
| configure.rses.STORAGE-3.protocols[0].<<.domains.wan.write | int | `1` |  |
| configure.rses.STORAGE-3.protocols[0].<<.extended_attributes | string | `"None"` |  |
| configure.rses.STORAGE-3.protocols[0].<<.impl | string | `"rucio.rse.protocols.gfal.Default"` |  |
| configure.rses.STORAGE-3.protocols[0].<<.port | int | `1094` |  |
| configure.rses.STORAGE-3.protocols[0].<<.prefix | string | `"//rucio"` |  |
| configure.rses.STORAGE-3.protocols[0].hostname | string | `"rucio-storage-3"` |  |
| configure.rses.STORAGE-3.protocols[0].scheme | string | `"davs"` |  |
| configure.rses.STORAGE-3.recreate_if_exists | bool | `true` |  |
| configure.run_database_migrations | bool | `true` |  |
| configure_rucio | bool | `true` | This will configure the rucio server with the storages |
| database | object | `{"default":"postgresql+psycopg://rucio:XcL0xT9FgFgJEc4i3OcQf2DMVKpjIWDGezqcIPmXlM@bdms-db:5432/rucio"}` | Databases Credentials used by Rucio to access the database. If postgresql subchart is deployed, these credentials should match those in postgresql.global.postgresql.auth. If postgresql subchart is not deployed, an external database must be provided |
| database.default | string | `"postgresql+psycopg://rucio:XcL0xT9FgFgJEc4i3OcQf2DMVKpjIWDGezqcIPmXlM@bdms-db:5432/rucio"` | The Rucio database connection URI |
| dev.client_image_tag | string | `nil` |  |
| dev.mount_repo | bool | `true` | mount the repository into the container, useful for development and debugging |
| dev.n_test_jobs | int | `1` | number of jobs to use for pytest |
| dev.run_tests | bool | `true` | run tests during helm test (otherwise, the tests can be run manually after exec into the pod) |
| dev.sleep | bool | `false` | sleep after test to allow interactive development |
| fts.enabled | bool | `true` | Specifies the configuration for FTS test step (FTS server, FTS database, and ActiveMQ broker containers). Enables or disables the deployment of a FTS instance for testing. This is set to 'False' if an external FTS is used |
| fts.ftsdb_password | string | `"SDP2RQkbJE2f+ohUb2nUu6Ae10BpQH0VD70CsIQcDtM"` | Defines the password for the FTS database user |
| fts.ftsdb_root_password | string | `"iB7dMiIybdoaozWZMkvRo0eg9HbQzG9+5up50zUDjE4"` | Defines the root password for the FTS database |
| fts.messaging.broker | string | `"localhost:61613"` |  |
| fts.messaging.password | string | `"topsecret"` |  |
| fts.messaging.use_broker_credentials | string | `"true"` |  |
| fts.messaging.username | string | `"fts"` |  |
| iam.bootstrap.config.users[0].cert.default_path | string | `"/tmp/usercert.pem"` |  |
| iam.bootstrap.config.users[0].cert.env_var | string | `"X509_USER_CERT"` |  |
| iam.bootstrap.config.users[0].cert.kind | string | `"env_var_file"` |  |
| iam.bootstrap.config.users[0].email | string | `"dpps@test.example"` |  |
| iam.bootstrap.config.users[0].family_name | string | `"User"` |  |
| iam.bootstrap.config.users[0].given_name | string | `"TestDpps"` |  |
| iam.bootstrap.config.users[0].groups[0] | string | `"ctao.dpps.test"` |  |
| iam.bootstrap.config.users[0].password | string | `"test-password"` |  |
| iam.bootstrap.config.users[0].role | string | `"ROLE_USER"` |  |
| iam.bootstrap.config.users[0].subject_dn | string | `"CN=DPPS User"` |  |
| iam.bootstrap.config.users[0].username | string | `"test-user"` |  |
| iam.bootstrap.config.users[1].cert.default_path | string | `"/tmp/user-unprivileged-cert.pem"` |  |
| iam.bootstrap.config.users[1].cert.env_var | string | `"X509_UNPRIVILEGED_DPPS_USER_CERT"` |  |
| iam.bootstrap.config.users[1].cert.kind | string | `"env_var_file"` |  |
| iam.bootstrap.config.users[1].email | string | `"unprivileged-dpps@test.example"` |  |
| iam.bootstrap.config.users[1].family_name | string | `"User"` |  |
| iam.bootstrap.config.users[1].given_name | string | `"TestUnprivilegedDpps"` |  |
| iam.bootstrap.config.users[1].groups[0] | string | `"alt_ctao.dpps.test"` |  |
| iam.bootstrap.config.users[1].password | string | `"test-password"` |  |
| iam.bootstrap.config.users[1].role | string | `"ROLE_USER"` |  |
| iam.bootstrap.config.users[1].subject_dn | string | `"CN=DPPS User Unprivileged"` |  |
| iam.bootstrap.config.users[1].username | string | `"test-user-unprivileged"` |  |
| iam.bootstrap.config.users[2].cert.default_path | string | `"/tmp/user-non-dpps-cert.pem"` |  |
| iam.bootstrap.config.users[2].cert.env_var | string | `"X509_NON_DPPS_USER_CERT"` |  |
| iam.bootstrap.config.users[2].cert.kind | string | `"env_var_file"` |  |
| iam.bootstrap.config.users[2].email | string | `"non-dpps@test.example"` |  |
| iam.bootstrap.config.users[2].family_name | string | `"User"` |  |
| iam.bootstrap.config.users[2].given_name | string | `"TestNonDpps"` |  |
| iam.bootstrap.config.users[2].groups | string | `nil` |  |
| iam.bootstrap.config.users[2].password | string | `"test-password"` |  |
| iam.bootstrap.config.users[2].role | string | `"ROLE_USER"` |  |
| iam.bootstrap.config.users[2].subject_dn | string | `"CN=Non-DPPS User"` |  |
| iam.bootstrap.config.users[2].username | string | `"test-user-non-dpps"` |  |
| iam.bootstrap.config.users[3].email | string | `"dpps@test.example"` |  |
| iam.bootstrap.config.users[3].family_name | string | `"User"` |  |
| iam.bootstrap.config.users[3].given_name | string | `"TestAdmin"` |  |
| iam.bootstrap.config.users[3].groups[0] | string | `"ctao.dpps.test"` |  |
| iam.bootstrap.config.users[3].password | string | `"test-password"` |  |
| iam.bootstrap.config.users[3].role | string | `"ROLE_ADMIN"` |  |
| iam.bootstrap.config.users[3].username | string | `"admin-user"` |  |
| iam.bootstrap.config.users[4].cert.default_path | string | `"/tmp/user-non-ctao-cert.pem"` |  |
| iam.bootstrap.config.users[4].cert.env_var | string | `"X509_NON-CTAO_USER_CERT"` |  |
| iam.bootstrap.config.users[4].cert.kind | string | `"env_var_file"` |  |
| iam.bootstrap.config.users[4].email | string | `"non-ctao@test.example"` |  |
| iam.bootstrap.config.users[4].family_name | string | `"User"` |  |
| iam.bootstrap.config.users[4].given_name | string | `"TestNonCTAO"` |  |
| iam.bootstrap.config.users[4].groups[0] | string | `"non-ctao.test"` |  |
| iam.bootstrap.config.users[4].password | string | `"test-password"` |  |
| iam.bootstrap.config.users[4].role | string | `"ROLE_USER"` |  |
| iam.bootstrap.config.users[4].subject_dn | string | `"CN=Non-CTAO User"` |  |
| iam.bootstrap.config.users[4].username | string | `"test-user-non-ctao"` |  |
| iam.bootstrap.env[0].name | string | `"X509_NON_DPPS_USER_CERT"` |  |
| iam.bootstrap.env[0].value | string | `"/tmp/user-non-dpps-cert.pem"` |  |
| iam.bootstrap.env[1].name | string | `"X509_UNPRIVILEGED_DPPS_USER_CERT"` |  |
| iam.bootstrap.env[1].value | string | `"/tmp/user-unprivileged-cert.pem"` |  |
| iam.bootstrap.env[2].name | string | `"X509_NON-CTAO_USER_CERT"` |  |
| iam.bootstrap.env[2].value | string | `"/tmp/user-non-ctao-cert.pem"` |  |
| iam.bootstrap.extraVolumeMounts[0].mountPath | string | `"/tmp/userkey.pem"` |  |
| iam.bootstrap.extraVolumeMounts[0].name | string | `"dppsuser-certkey-400"` |  |
| iam.bootstrap.extraVolumeMounts[0].subPath | string | `"dppsuser.key.pem"` |  |
| iam.bootstrap.extraVolumeMounts[1].mountPath | string | `"/tmp/usercert.pem"` |  |
| iam.bootstrap.extraVolumeMounts[1].name | string | `"dppsuser-certkey-600"` |  |
| iam.bootstrap.extraVolumeMounts[1].subPath | string | `"dppsuser.pem"` |  |
| iam.bootstrap.extraVolumeMounts[2].mountPath | string | `"/tmp/user-unprivileged-key.pem"` |  |
| iam.bootstrap.extraVolumeMounts[2].name | string | `"dppsuser-unprivileged-certkey-400"` |  |
| iam.bootstrap.extraVolumeMounts[2].subPath | string | `"dppsuser.key.pem"` |  |
| iam.bootstrap.extraVolumeMounts[3].mountPath | string | `"/tmp/user-unprivileged-cert.pem"` |  |
| iam.bootstrap.extraVolumeMounts[3].name | string | `"dppsuser-unprivileged-certkey-600"` |  |
| iam.bootstrap.extraVolumeMounts[3].subPath | string | `"dppsuser.pem"` |  |
| iam.bootstrap.extraVolumeMounts[4].mountPath | string | `"/tmp/user-non-dpps-key.pem"` |  |
| iam.bootstrap.extraVolumeMounts[4].name | string | `"dppsuser-non-dpps-certkey-400"` |  |
| iam.bootstrap.extraVolumeMounts[4].subPath | string | `"dppsuser.key.pem"` |  |
| iam.bootstrap.extraVolumeMounts[5].mountPath | string | `"/tmp/user-non-dpps-cert.pem"` |  |
| iam.bootstrap.extraVolumeMounts[5].name | string | `"dppsuser-non-dpps-certkey-600"` |  |
| iam.bootstrap.extraVolumeMounts[5].subPath | string | `"dppsuser.pem"` |  |
| iam.bootstrap.extraVolumeMounts[6].mountPath | string | `"/tmp/user-non-ctao-key.pem"` |  |
| iam.bootstrap.extraVolumeMounts[6].name | string | `"dppsuser-non-ctao-certkey-400"` |  |
| iam.bootstrap.extraVolumeMounts[6].subPath | string | `"dppsuser.key.pem"` |  |
| iam.bootstrap.extraVolumeMounts[7].mountPath | string | `"/tmp/user-non-ctao-cert.pem"` |  |
| iam.bootstrap.extraVolumeMounts[7].name | string | `"dppsuser-non-ctao-certkey-600"` |  |
| iam.bootstrap.extraVolumeMounts[7].subPath | string | `"dppsuser.pem"` |  |
| iam.bootstrap.extraVolumes[0].name | string | `"dppsuser-certkey"` |  |
| iam.bootstrap.extraVolumes[0].secret.defaultMode | int | `420` |  |
| iam.bootstrap.extraVolumes[0].secret.secretName | string | `"bdms-dppsuser-certkey"` |  |
| iam.bootstrap.extraVolumes[10].name | string | `"dppsuser-non-ctao-certkey-400"` |  |
| iam.bootstrap.extraVolumes[10].secret.defaultMode | int | `256` |  |
| iam.bootstrap.extraVolumes[10].secret.secretName | string | `"bdms-dppsuser-non-ctao-certkey"` |  |
| iam.bootstrap.extraVolumes[1].name | string | `"dppsuser-certkey-600"` |  |
| iam.bootstrap.extraVolumes[1].secret.defaultMode | int | `256` |  |
| iam.bootstrap.extraVolumes[1].secret.secretName | string | `"bdms-dppsuser-certkey"` |  |
| iam.bootstrap.extraVolumes[2].name | string | `"dppsuser-certkey-400"` |  |
| iam.bootstrap.extraVolumes[2].secret.defaultMode | int | `256` |  |
| iam.bootstrap.extraVolumes[2].secret.secretName | string | `"bdms-dppsuser-certkey"` |  |
| iam.bootstrap.extraVolumes[3].name | string | `"dppsuser-unprivileged-certkey"` |  |
| iam.bootstrap.extraVolumes[3].secret.defaultMode | int | `420` |  |
| iam.bootstrap.extraVolumes[3].secret.secretName | string | `"bdms-dppsuser-unprivileged-certkey"` |  |
| iam.bootstrap.extraVolumes[4].name | string | `"dppsuser-unprivileged-certkey-600"` |  |
| iam.bootstrap.extraVolumes[4].secret.defaultMode | int | `384` |  |
| iam.bootstrap.extraVolumes[4].secret.secretName | string | `"bdms-dppsuser-unprivileged-certkey"` |  |
| iam.bootstrap.extraVolumes[5].name | string | `"dppsuser-unprivileged-certkey-400"` |  |
| iam.bootstrap.extraVolumes[5].secret.defaultMode | int | `256` |  |
| iam.bootstrap.extraVolumes[5].secret.secretName | string | `"bdms-dppsuser-unprivileged-certkey"` |  |
| iam.bootstrap.extraVolumes[6].name | string | `"dppsuser-non-dpps-certkey"` |  |
| iam.bootstrap.extraVolumes[6].secret.defaultMode | int | `420` |  |
| iam.bootstrap.extraVolumes[6].secret.secretName | string | `"bdms-dppsuser-non-dpps-certkey"` |  |
| iam.bootstrap.extraVolumes[7].name | string | `"dppsuser-non-dpps-certkey-600"` |  |
| iam.bootstrap.extraVolumes[7].secret.defaultMode | int | `384` |  |
| iam.bootstrap.extraVolumes[7].secret.secretName | string | `"bdms-dppsuser-non-dpps-certkey"` |  |
| iam.bootstrap.extraVolumes[8].name | string | `"dppsuser-non-dpps-certkey-400"` |  |
| iam.bootstrap.extraVolumes[8].secret.defaultMode | int | `256` |  |
| iam.bootstrap.extraVolumes[8].secret.secretName | string | `"bdms-dppsuser-non-dpps-certkey"` |  |
| iam.bootstrap.extraVolumes[9].name | string | `"dppsuser-non-ctao-certkey-600"` |  |
| iam.bootstrap.extraVolumes[9].secret.defaultMode | int | `384` |  |
| iam.bootstrap.extraVolumes[9].secret.secretName | string | `"bdms-dppsuser-non-ctao-certkey"` |  |
| iam.bootstrap.image.pullPolicy | string | `"IfNotPresent"` |  |
| iam.bootstrap.image.repository | string | `"harbor.cta-observatory.org/dpps/dpps-iam-client"` |  |
| iam.bootstrap.image.tag | string | `nil` |  |
| iam.bootstrap.tag | string | `nil` |  |
| iam.cert-generator-grid.enabled | bool | `false` |  |
| iam.dev.client_image_tag | string | `nil` |  |
| iam.enabled | bool | `true` |  |
| iam.iam.ingress.annotations."nginx.ingress.kubernetes.io/ssl-passthrough" | string | `"true"` |  |
| iam.iam.ingress.annotations."nginx.ingress.kubernetes.io/ssl-redirect" | string | `"true"` |  |
| iam.iam.ingress.className | string | `"nginx"` |  |
| iam.iam.ingress.enabled | bool | `true` |  |
| iam.iam.ingress.tls.enabled | bool | `true` |  |
| iam.iam.ingress.tls.secretName | string | `"bdms-tls"` |  |
| iam.iam.loginService.config.java.opts | string | `"-Xms512m -Xmx512m -Djava.security.egd=file:/dev/./urandom -Dspring.profiles.active=prod -Dlogging.level.org.springframework.web=DEBUG -Dlogging.level.com.indigo=DEBUG"` |  |
| iam.iam.mysql.enabled | bool | `false` |  |
| iam.nameOverride | string | `"dpps-iam"` |  |
| iam.vomsAA.config.host | string | `"voms.test.example"` |  |
| iam.vomsAA.config.voName | string | `"ctao.dpps.test"` |  |
| iam.vomsAA.deployment.replicas | int | `1` |  |
| iam.vomsAA.enabled | bool | `true` |  |
| iam.vomsAA.ingress.className | string | `"nginx"` |  |
| iam.vomsAA.ingress.enabled | bool | `true` |  |
| iam.vomsAA.ingress.tls.enabled | bool | `true` |  |
| iam.vomsAA.lsc.entries[0] | string | `"/CN=voms.test.example"` |  |
| iam.vomsAA.lsc.entries[1] | string | `"/CN=DPPS Development CA"` |  |
| iam.vomsAA.nginxVoms.resources.limits.memory | string | `"256Mi"` |  |
| iam.vomsAA.nginxVoms.resources.requests.cpu | string | `"100m"` |  |
| iam.vomsAA.nginxVoms.resources.requests.memory | string | `"128Mi"` |  |
| iam.vomsAA.resources.limits.cpu | string | `"500m"` |  |
| iam.vomsAA.resources.limits.memory | string | `"1Gi"` |  |
| iam.vomsAA.resources.requests.cpu | string | `"200m"` |  |
| iam.vomsAA.resources.requests.memory | string | `"512Mi"` |  |
| postgresql.enabled | bool | `true` | Configuration of built-in postgresql database. If 'enabled: true', a postgresql instance will be deployed, otherwise, an external database must be provided in database.default value |
| postgresql.global.postgresql.auth.database | string | `"rucio"` | The name of the database to be created and used by Rucio |
| postgresql.global.postgresql.auth.password | string | `"XcL0xT9FgFgJEc4i3OcQf2DMVKpjIWDGezqcIPmXlM"` | The password for the database user |
| postgresql.global.postgresql.auth.username | string | `"rucio"` | The database username for authentication |
| postgresql.image.registry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| postgresql.image.repository | string | `"bitnamilegacy/postgresql"` |  |
| prepuller_enabled | bool | `true` | Starts containers with the same image as the one used in the deployment before all volumes are available. Saves time in the first deployment |
| prod_tests.config | object | `{"data_prefix":"/storage-1/ctao.dpps.test/tests/","file_size_mb":1,"interval_between_new_files_seconds":2,"number_of_files":10,"vo_name":"ctao.dpps.test","wait_after_end_of_file_creation_interval_seconds":1,"wait_after_end_of_file_creation_seconds":30}` | Configuration for production tests |
| prod_tests.config.data_prefix | string | `"/storage-1/ctao.dpps.test/tests/"` | must include the voi and scope directory below the RSE prefix |
| prod_tests.enabled | bool | `false` | Enable or disable production tests during helm test |
| prod_tests.volumeMounts[0].mountPath | string | `"/storage-1/"` |  |
| prod_tests.volumeMounts[0].name | string | `"storage-1-data"` |  |
| prod_tests.volumeMounts[1].mountPath | string | `"/etc/grid-security/ca.pem"` |  |
| prod_tests.volumeMounts[1].name | string | `"cafile"` |  |
| prod_tests.volumeMounts[1].subPath | string | `"ca.pem"` |  |
| prod_tests.volumeMounts[2].mountPath | string | `"/opt/rucio/etc/userkey.pem"` |  |
| prod_tests.volumeMounts[2].name | string | `"dppsuser-certkey-400"` |  |
| prod_tests.volumeMounts[2].subPath | string | `"dppsuser.key.pem"` |  |
| prod_tests.volumeMounts[3].mountPath | string | `"/opt/rucio/etc/usercert.pem"` |  |
| prod_tests.volumeMounts[3].name | string | `"dppsuser-certkey-600"` |  |
| prod_tests.volumeMounts[3].subPath | string | `"dppsuser.pem"` |  |
| prod_tests.volumeMounts[4].mountPath | string | `"/opt/rucio/etc/nondppsuserkey.pem"` |  |
| prod_tests.volumeMounts[4].name | string | `"dppsuser-non-dpps-certkey-400"` |  |
| prod_tests.volumeMounts[4].subPath | string | `"dppsuser.key.pem"` |  |
| prod_tests.volumeMounts[5].mountPath | string | `"/opt/rucio/etc/nondppsusercert.pem"` |  |
| prod_tests.volumeMounts[5].name | string | `"dppsuser-non-dpps-certkey-600"` |  |
| prod_tests.volumeMounts[5].subPath | string | `"dppsuser.pem"` |  |
| prod_tests.volumeMounts[6].mountPath | string | `"/opt/rucio/etc/unprivilegeduserkey.pem"` |  |
| prod_tests.volumeMounts[6].name | string | `"dppsuser-unprivileged-certkey-400"` |  |
| prod_tests.volumeMounts[6].subPath | string | `"dppsuser.key.pem"` |  |
| prod_tests.volumeMounts[7].mountPath | string | `"/opt/rucio/etc/unprivilegedusercert.pem"` |  |
| prod_tests.volumeMounts[7].name | string | `"dppsuser-unprivileged-certkey-600"` |  |
| prod_tests.volumeMounts[7].subPath | string | `"dppsuser.pem"` |  |
| prod_tests.volumeMounts[8].mountPath | string | `"/opt/rucio/etc/nonctaouserkey.pem"` |  |
| prod_tests.volumeMounts[8].name | string | `"dppsuser-non-ctao-certkey-400"` |  |
| prod_tests.volumeMounts[8].subPath | string | `"dppsuser.key.pem"` |  |
| prod_tests.volumeMounts[9].mountPath | string | `"/opt/rucio/etc/nonctaousercert.pem"` |  |
| prod_tests.volumeMounts[9].name | string | `"dppsuser-non-ctao-certkey-600"` |  |
| prod_tests.volumeMounts[9].subPath | string | `"dppsuser.pem"` |  |
| prod_tests.volumes[0].name | string | `"storage-1-data"` |  |
| prod_tests.volumes[0].persistentVolumeClaim.claimName | string | `"storage-1-pvc"` |  |
| prod_tests.volumes[10].name | string | `"dppsuser-unprivileged-certkey-400"` |  |
| prod_tests.volumes[10].secret.defaultMode | int | `256` |  |
| prod_tests.volumes[10].secret.secretName | string | `"bdms-dppsuser-unprivileged-certkey"` |  |
| prod_tests.volumes[11].name | string | `"dppsuser-non-ctao-certkey-600"` |  |
| prod_tests.volumes[11].secret.defaultMode | int | `384` |  |
| prod_tests.volumes[11].secret.secretName | string | `"bdms-dppsuser-non-ctao-certkey"` |  |
| prod_tests.volumes[12].name | string | `"dppsuser-non-ctao-certkey-400"` |  |
| prod_tests.volumes[12].secret.defaultMode | int | `256` |  |
| prod_tests.volumes[12].secret.secretName | string | `"bdms-dppsuser-non-ctao-certkey"` |  |
| prod_tests.volumes[1].name | string | `"cafile"` |  |
| prod_tests.volumes[1].secret.defaultMode | int | `420` |  |
| prod_tests.volumes[1].secret.secretName | string | `"bdms-server-cafile"` |  |
| prod_tests.volumes[2].name | string | `"dppsuser-certkey"` |  |
| prod_tests.volumes[2].secret.defaultMode | int | `420` |  |
| prod_tests.volumes[2].secret.secretName | string | `"bdms-dppsuser-certkey"` |  |
| prod_tests.volumes[3].configMap.name | string | `"bdms-scripts"` |  |
| prod_tests.volumes[3].name | string | `"scripts"` |  |
| prod_tests.volumes[4].name | string | `"dppsuser-certkey-600"` |  |
| prod_tests.volumes[4].secret.defaultMode | int | `384` |  |
| prod_tests.volumes[4].secret.secretName | string | `"bdms-dppsuser-certkey"` |  |
| prod_tests.volumes[5].name | string | `"dppsuser-certkey-400"` |  |
| prod_tests.volumes[5].secret.defaultMode | int | `256` |  |
| prod_tests.volumes[5].secret.secretName | string | `"bdms-dppsuser-certkey"` |  |
| prod_tests.volumes[6].name | string | `"dppsuser-non-dpps-certkey"` |  |
| prod_tests.volumes[6].secret.defaultMode | int | `420` |  |
| prod_tests.volumes[6].secret.secretName | string | `"bdms-dppsuser-non-dpps-certkey"` |  |
| prod_tests.volumes[7].name | string | `"dppsuser-non-dpps-certkey-600"` |  |
| prod_tests.volumes[7].secret.defaultMode | int | `384` |  |
| prod_tests.volumes[7].secret.secretName | string | `"bdms-dppsuser-non-dpps-certkey"` |  |
| prod_tests.volumes[8].name | string | `"dppsuser-non-dpps-certkey-400"` |  |
| prod_tests.volumes[8].secret.defaultMode | int | `256` |  |
| prod_tests.volumes[8].secret.secretName | string | `"bdms-dppsuser-non-dpps-certkey"` |  |
| prod_tests.volumes[9].name | string | `"dppsuser-unprivileged-certkey-600"` |  |
| prod_tests.volumes[9].secret.defaultMode | int | `384` |  |
| prod_tests.volumes[9].secret.secretName | string | `"bdms-dppsuser-unprivileged-certkey"` |  |
| redis.architecture | string | `"standalone"` |  |
| redis.auth.enabled | bool | `false` |  |
| redis.enabled | bool | `true` |  |
| redis.global.security.allowInsecureImages | bool | `true` |  |
| redis.image.registry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| redis.image.repository | string | `"bitnamilegacy/redis"` |  |
| redis.master.persistence.enabled | bool | `true` |  |
| redis.master.persistence.size | string | `"8Gi"` |  |
| redis.master.resources.limits.cpu | string | `"500m"` |  |
| redis.master.resources.limits.memory | string | `"512Mi"` |  |
| redis.master.resources.requests.cpu | string | `"100m"` |  |
| redis.master.resources.requests.memory | string | `"256Mi"` |  |
| rucio-daemons.config.common.extract_scope | string | `"ctao_bdms"` |  |
| rucio-daemons.config.conveyor.scheme | string | `"davs,root,srm,gsiftp,http,https"` |  |
| rucio-daemons.config.database.default | string | `"postgresql+psycopg://rucio:XcL0xT9FgFgJEc4i3OcQf2DMVKpjIWDGezqcIPmXlM@bdms-db:5432/rucio"` | Specifies the connection URI for the Rucio database, these settings will be written to 'rucio.cfg' |
| rucio-daemons.config.messaging-fts3.brokers | string | `"fts-activemq"` | Specifies the message broker used for FTS messaging |
| rucio-daemons.config.messaging-fts3.destination | string | `"/topic/transfer.fts_monitoring_complete"` | Specifies the message broker queue path where FTS sends transfer status updates. This is the place where Rucio listens for completed transfer notifications |
| rucio-daemons.config.messaging-fts3.nonssl_port | int | `61613` | Specifies the non-SSL port |
| rucio-daemons.config.messaging-fts3.password | string | `"topsecret"` | Specifies the authentication credential (password) for connecting to the message broker |
| rucio-daemons.config.messaging-fts3.port | int | `61613` | Defines the port used for the broker |
| rucio-daemons.config.messaging-fts3.use_ssl | bool | `false` | Determines whether to use SSL for message broker connections. If true, valid certificates are required for securing the connection |
| rucio-daemons.config.messaging-fts3.username | string | `"fts"` | Specifies the authentication credential (username) for connecting to the message broker |
| rucio-daemons.config.messaging-fts3.voname | string | `"ctao"` |  |
| rucio-daemons.config.policy.lfn2pfn_algorithm_default | string | `"ctao_bdms"` |  |
| rucio-daemons.config.policy.package | string | `"bdms_rucio_policy"` | Defines the policy permission model for Rucio for determining how authorization and access controls are applied, its value should be taken from the installed Rucio policy package |
| rucio-daemons.config.policy.permission | string | `"ctao"` |  |
| rucio-daemons.config.policy.schema | string | `"ctao_bdms"` |  |
| rucio-daemons.conveyorFinisher.activities | string | `"'User Subscriptions'"` | Specifies which Rucio activities to be handled. Some of the activities for data movements are 'User Subscriptions' and 'Production Transfers' |
| rucio-daemons.conveyorFinisher.resources.limits.cpu | string | `"3000m"` |  |
| rucio-daemons.conveyorFinisher.resources.limits.memory | string | `"4Gi"` |  |
| rucio-daemons.conveyorFinisher.resources.requests.cpu | string | `"100m"` |  |
| rucio-daemons.conveyorFinisher.resources.requests.memory | string | `"200Mi"` |  |
| rucio-daemons.conveyorFinisher.sleepTime | int | `5` | Defines how often (in seconds) the daemon processes finished transfers |
| rucio-daemons.conveyorFinisherCount | int | `1` | Marks completed transfers and updates metadata |
| rucio-daemons.conveyorPoller.activities | string | `"'User Subscriptions'"` | Specifies which Rucio activities to be handled. Some of the activities for data movements are 'User Subscriptions' and 'Production Transfers' |
| rucio-daemons.conveyorPoller.olderThan | int | `600` | Filters transfers that are older than the specified time (in seconds) before polling |
| rucio-daemons.conveyorPoller.resources.limits.cpu | string | `"3000m"` |  |
| rucio-daemons.conveyorPoller.resources.limits.memory | string | `"4Gi"` |  |
| rucio-daemons.conveyorPoller.resources.requests.cpu | string | `"100m"` |  |
| rucio-daemons.conveyorPoller.resources.requests.memory | string | `"200Mi"` |  |
| rucio-daemons.conveyorPoller.sleepTime | int | `60` | Defines how often (in seconds) the daemon polls for transfer status updates |
| rucio-daemons.conveyorPollerCount | int | `1` | Polls FTS to check the status of ongoing transfers |
| rucio-daemons.conveyorReceiverCount | int | `1` | Listens to messages from ActiveMQ, which FTS uses to publish transfer status updates. This ensures Rucio is notified of completed or failed transfers in real time |
| rucio-daemons.conveyorTransferSubmitter.activities | string | `"'User Subscriptions'"` | Specifies which Rucio activities to be handled. Some of the activities for data movements are 'User Subscriptions' and 'Production Transfers' |
| rucio-daemons.conveyorTransferSubmitter.archiveTimeout | string | `""` | Sets the timeout if required for archiving completed transfers |
| rucio-daemons.conveyorTransferSubmitter.resources.limits.cpu | string | `"3000m"` |  |
| rucio-daemons.conveyorTransferSubmitter.resources.limits.memory | string | `"4Gi"` |  |
| rucio-daemons.conveyorTransferSubmitter.resources.requests.cpu | string | `"100m"` |  |
| rucio-daemons.conveyorTransferSubmitter.resources.requests.memory | string | `"200Mi"` |  |
| rucio-daemons.conveyorTransferSubmitter.sleepTime | int | `5` | Defines the interval (in seconds) the daemon waits before checking for new transfers |
| rucio-daemons.conveyorTransferSubmitterCount | int | `1` | Number of container instances to deploy for each Rucio daemon, this daemon submits new transfer requests to the FTS |
| rucio-daemons.enabled | bool | `true` |  |
| rucio-daemons.ftsRenewal.additionalEnvs[0].name | string | `"USERCERT_NAME"` |  |
| rucio-daemons.ftsRenewal.additionalEnvs[0].value | string | `"usercert.pem"` |  |
| rucio-daemons.ftsRenewal.additionalEnvs[1].name | string | `"USERKEY_NAME"` |  |
| rucio-daemons.ftsRenewal.additionalEnvs[1].value | string | `"userkey.pem"` |  |
| rucio-daemons.ftsRenewal.enabled | bool | `true` |  |
| rucio-daemons.ftsRenewal.extraSecretMounts | list | `[]` |  |
| rucio-daemons.ftsRenewal.image.repository | string | `"harbor.cta-observatory.org/proxy_cache/rucio/fts-cron"` |  |
| rucio-daemons.ftsRenewal.image.tag | string | `"38.2.0"` |  |
| rucio-daemons.ftsRenewal.schedule | string | `"0 */6 * * *"` |  |
| rucio-daemons.ftsRenewal.script | string | `"default"` |  |
| rucio-daemons.ftsRenewal.secretMounts[0].mountPath | string | `"/etc/grid-security/certificates/74df993b.0"` |  |
| rucio-daemons.ftsRenewal.secretMounts[0].secretName | string | `"server-cafile"` |  |
| rucio-daemons.ftsRenewal.secretMounts[0].subPath | string | `"ca.pem"` |  |
| rucio-daemons.ftsRenewal.secretMounts[0].volumeName | string | `"ca-cert"` |  |
| rucio-daemons.ftsRenewal.secretMounts[1].mountPath | string | `"/etc/grid-security/certificates/74df993b.r0"` |  |
| rucio-daemons.ftsRenewal.secretMounts[1].secretName | string | `"server-cafile"` |  |
| rucio-daemons.ftsRenewal.secretMounts[1].subPath | string | `"dpps_test_ca.crl.r0"` |  |
| rucio-daemons.ftsRenewal.secretMounts[1].volumeName | string | `"ca-crl"` |  |
| rucio-daemons.ftsRenewal.secretMounts[2].mountPath | string | `"/opt/rucio/certs/usercert.pem"` |  |
| rucio-daemons.ftsRenewal.secretMounts[2].secretName | string | `"dppsuser-certkey"` |  |
| rucio-daemons.ftsRenewal.secretMounts[2].subPath | string | `"dppsuser.pem"` |  |
| rucio-daemons.ftsRenewal.secretMounts[2].volumeName | string | `"dppsuser-cert"` |  |
| rucio-daemons.ftsRenewal.secretMounts[3].mountPath | string | `"/opt/rucio/keys/userkey.pem"` |  |
| rucio-daemons.ftsRenewal.secretMounts[3].secretName | string | `"dppsuser-certkey"` |  |
| rucio-daemons.ftsRenewal.secretMounts[3].subPath | string | `"dppsuser.key.pem"` |  |
| rucio-daemons.ftsRenewal.secretMounts[3].volumeName | string | `"dppsuser-key"` |  |
| rucio-daemons.ftsRenewal.servers | string | `"https://bdms-fts:8446"` |  |
| rucio-daemons.image.pullPolicy | string | `"IfNotPresent"` | It defines when kubernetes should pull the container image, the options available are: Always, IfNotPresent, and Never |
| rucio-daemons.image.repository | string | `"harbor.cta-observatory.org/dpps/bdms-rucio-daemons"` | Specifies the container image repository for Rucio daemons |
| rucio-daemons.image.tag | string | `"39.0.0-v0.5.0"` | Specific image tag to use for deployment |
| rucio-daemons.judgeEvaluator.resources.limits.cpu | string | `"3000m"` |  |
| rucio-daemons.judgeEvaluator.resources.limits.memory | string | `"4Gi"` |  |
| rucio-daemons.judgeEvaluator.resources.requests.cpu | string | `"100m"` |  |
| rucio-daemons.judgeEvaluator.resources.requests.memory | string | `"1Gi"` |  |
| rucio-daemons.judgeEvaluatorCount | int | `1` | Evaluates Rucio replication rules and triggers transfers |
| rucio-daemons.secretMounts[0].mountPath | string | `"/opt/certs/ca.pem"` |  |
| rucio-daemons.secretMounts[0].secretName | string | `"server-cafile"` |  |
| rucio-daemons.secretMounts[0].subPath | string | `"ca.pem"` |  |
| rucio-daemons.secretMounts[1].mountPath | string | `"/opt/proxy/x509up"` |  |
| rucio-daemons.secretMounts[1].secretName | string | `"rucio-x509up"` |  |
| rucio-daemons.secretMounts[1].subPath | string | `"x509up"` |  |
| rucio-daemons.useDeprecatedImplicitSecrets | bool | `false` |  |
| rucio-server.authRucioHost | string | `"rucio-server.local"` | The hostname of the Rucio authentication server. |
| rucio-server.config.common.extract_scope | string | `"ctao_bdms"` |  |
| rucio-server.config.database.default | string | `"postgresql+psycopg://rucio:XcL0xT9FgFgJEc4i3OcQf2DMVKpjIWDGezqcIPmXlM@bdms-db:5432/rucio"` | The database connection URI for Rucio |
| rucio-server.config.policy.lfn2pfn_algorithm_default | string | `"ctao_bdms"` |  |
| rucio-server.config.policy.package | string | `"bdms_rucio_policy"` | Defines the policy permission model for Rucio for determining how authorization and access controls are applied, its value should be taken from the installed Rucio policy package |
| rucio-server.config.policy.permission | string | `"ctao"` |  |
| rucio-server.config.policy.schema | string | `"ctao_bdms"` |  |
| rucio-server.enabled | bool | `true` |  |
| rucio-server.errorLog.image | string | `"harbor.cta-observatory.org/proxy_cache/busybox"` |  |
| rucio-server.httpd_config.encoded_slashes | string | `"True"` | Allows for custom LFNs with slashes in request URLs so that Rucio server (Apache) can decode and handle such requests properly |
| rucio-server.httpd_config.encoded_slashes_no_decode | string | `"True"` | Needed for urls with /, e.g. did rest api |
| rucio-server.httpd_config.grid_site_enabled | string | `"True"` | Enables Rucio server to support and interact with grid middleware (storages) for X509 authentication with proxies |
| rucio-server.image.pullPolicy | string | `"IfNotPresent"` | It defines when kubernetes should pull the container image, the options available are: Always, IfNotPresent, and Never |
| rucio-server.image.repository | string | `"harbor.cta-observatory.org/dpps/bdms-rucio-server"` | The container image repository for Rucio server with the CTAO Rucio policy package installed |
| rucio-server.image.tag | string | `"39.0.0-v0.5.0"` | The specific image tag to deploy |
| rucio-server.ingress.enabled | bool | `false` |  |
| rucio-server.replicaCount | int | `1` | Number of replicas of the Rucio server to deploy. We can increase it to meet higher availability goals |
| rucio-server.service.name | string | `"https"` | The name of the service port |
| rucio-server.service.port | int | `443` | The port exposed by the kubernetes service, making the Rucio server accessible within the cluster |
| rucio-server.service.protocol | string | `"TCP"` | The network protocol used for HTTPS based communication |
| rucio-server.service.targetPort | int | `443` | The port inside the Rucio server container that listens for incoming traffic |
| rucio-server.service.type | string | `"ClusterIP"` | Specifies the kubernetes service type for making the Rucio server accessible within or outside the kubernetes cluster, available options include clusterIP (internal access only, default), NodePort (exposes the service on port across all cluster nodes), and LoadBalancer (Uses an external load balancer) |
| rucio-server.useSSL | bool | `true` | Enables the Rucio server to use SSL/TLS for secure communication, requiring valid certificates to be configured |
| rucio.password | string | `"secret"` |  |
| rucio.username | string | `"dpps"` | Specifies the username for Rucio operations as part of Rucio configuration |
| rucio.version | string | `"38.2.0"` | The version of Rucio being deployed |
| rucio_client_config.configMapName | string | `nil` | The name of the ConfigMap that contains the Rucio configuration.  If empty, default name will be used |
| rucio_client_config.createConfigMap | bool | `true` | If true, creates a ConfigMap with the Rucio configuration |
| rucio_iam_sync_user.enabled | bool | `true` |  |
| rucio_iam_sync_user.iam_server | string | `"http://{{ include \"dpps-iam.fullname\" . }}-dpps-iam-login-service:8080"` | The IAM server URL for Rucio IAM synchronization, can be templated |
| rucio_iam_sync_user.image.repository | string | `"harbor.cta-observatory.org/dpps/bdms-client"` |  |
| rucio_iam_sync_user.image.tag | string | `nil` |  |
| rucio_iam_sync_user.secret.client_id | string | `nil` |  |
| rucio_iam_sync_user.secret.client_secret | string | `nil` |  |
| rucio_iam_sync_user.secret.create | bool | `true` | Create secret from values, for testing. Set to false for production and create secret |
| rucio_iam_sync_user.secret.name | string | `"sync-rucio-iam-config"` | name of the secret containing the sync config file in key sync-iam-rucio.cfg |
| safe_to_bootstrap_rucio | bool | `false` | This is a destructive operation, it will delete all data in the database |
| safe_to_bootstrap_rucio_on_install | bool | `true` | This is will delete all data in the database only on the first install |
| suffix_namespace | string | `"default"` | Specifies the Namespace suffix used for managing deployments in kubernetes |
| test_storages | object | `{"enabled":true,"xrootd":{"image":{"repository":"harbor.cta-observatory.org/proxy_cache/rucio/test-xrootd","tag":"38.2.0"},"instances":["rucio-storage-1","rucio-storage-2","rucio-storage-3"],"rucio_storage_1_storage_class":"standard"}}` | - A list of test storages, deployed in the test setup |
| test_storages.enabled | bool | `true` | If true, deploys test storages for testing purposes. This is set to 'False' if an external storage is used as in the production setup |
| test_storages.xrootd.image.repository | string | `"harbor.cta-observatory.org/proxy_cache/rucio/test-xrootd"` | The container image repository for the XRootD storage deployment |
| test_storages.xrootd.image.tag | string | `"38.2.0"` | Defines the specific version of the XRootD image to use |
| test_storages.xrootd.rucio_storage_1_storage_class | string | `"standard"` | The storage class name for the PVC used by rucio-storage-1 |

