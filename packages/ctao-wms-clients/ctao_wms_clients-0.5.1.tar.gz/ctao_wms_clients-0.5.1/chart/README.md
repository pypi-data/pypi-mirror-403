# wms

![Version: 0.0.0-dev](https://img.shields.io/badge/Version-0.0.0--dev-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: dev](https://img.shields.io/badge/AppVersion-dev-informational?style=flat-square)

A Helm chart to deploy the Workload Management System of CTAO

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://diracgrid.github.io/diracx-charts | diracx | 1.0.0 |
| oci://harbor.cta-observatory.org/dpps | cert-generator-grid | v3.3.0-rc1 |
| oci://harbor.cta-observatory.org/dpps | cvmfs | v0.6.0 |
| oci://harbor.cta-observatory.org/dpps | iam(dpps-iam) | v0.1.1 |
| oci://harbor.cta-observatory.org/proxy_cache/bitnamicharts | mariadb | 20.5.5 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` |  |
| cert-generator-grid | object | `{"enabled":true,"extra_server_names":["iam.test.example","voms.test.example","fts","opensearch-cluster-master","dirac-master-cs","dirac-ce","dirac-web-app","dirac-client","dirac-proxy-manager","dirac-bundle-delivery","dirac-system-admin","dirac-component-monitoring","dirac-job-manager","dirac-job-monitoring","dirac-job-state-update","dirac-wms-admin","dirac-matcher","dirac-pilot-manager","dirac-pilot-status","dirac-optimization-mind","dirac-sandbox-store","dirac-file-catalog","dirac-storage-element","dirac-req-proxy","dirac-resource-status","dirac-resource-management","dirac-publisher","dirac-req-executing","dirac-req-manager","dirac-clean-req-db","dirac-site-director","dirac-pilot-sync","dirac-optimizers"],"generatePreHooks":true,"users":[{"name":"DPPS User","suffix":""},{"name":"DPPS User Unprivileged","suffix":"-unprivileged"},{"name":"Non-DPPS User","suffix":"-non-dpps"}]}` | Settings for the certificate generator |
| cvmfs | object | `{"enabled":true,"publish_docker_images":["harbor.cta-observatory.org/proxy_cache/library/python:3.12-slim"],"publisher":{"image":{"repository_prefix":"harbor.cta-observatory.org/proxy_cache/bitnamilegacy/kubectl","tag":"1.31.1"}}}` | Configuration for the cvmfs subchart, included for testing |
| dev | object | `{"client_image_tag":null,"mount_repo":true,"run_tests":true,"sleep":false}` | Settings for local development |
| dev.client_image_tag | string | `nil` | tag of the image used to run helm tests |
| dev.mount_repo | bool | `true` | mount the repo volume to test the code as it is being developed |
| dev.run_tests | bool | `true` | run tests in the container |
| dev.sleep | bool | `false` | sleep after test to allow interactive development |
| diracCE | object | `{"enabled":true,"extraVolumes":[],"hostkey":{"secretFullName":""},"resources":{}}` | A simple SSH compute element for testing |
| diracClient.hostkey.secretFullName | string | `""` |  |
| diracDatabases | object | `{"createSecret":true,"host":"dirac-db","password":"dirac-db","port":"3306","rootPassword":"dirac-db-root","rootUser":"root","secretName":"dirac-db-password","user":"Dirac"}` | SQL database use by DIRAC |
| diracServer | object | `{"bootstrap":{"componentMonitoring":true,"enabled":true,"firstProxy":true,"image":"harbor.cta-observatory.org/proxy_cache/bitnamilegacy/kubectl:1.33.1","initDiracDb":true,"syncDiracxCS":true,"syncIamUsers":true,"syncRSS":true},"configmap":{"create":true,"excludeFromMasterCSStartup":"(\"masterCS.cfg\" \"baseDirac.cfg\" \"webApp.cfg\" \"DIRAC.cfg\")","name":null},"configurationName":"DPPS-Tests","diracComponents":{"_agentDefaults":{"port":null,"replicaCount":1,"type":"agent"},"_executorDefaults":{"port":null,"replicaCount":1,"type":"executor"},"_serviceDefaults":{"replicaCount":1,"type":"service"},"bundleDelivery":{"<<":{"replicaCount":1,"type":"service"},"cmd":"Framework/BundleDelivery","port":9158},"cleanReqDB":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"RequestManagement/CleanReqDBAgent","port":null},"componentMonitoring":{"<<":{"replicaCount":1,"type":"service"},"cmd":"Framework/ComponentMonitoring","port":9190},"fileCatalog":{"<<":{"replicaCount":1,"type":"service"},"cmd":"DataManagement/FileCatalog","port":9197},"jobManager":{"cmd":"WorkloadManagement/JobManager","port":9132,"replicaCount":1,"type":"service"},"jobMonitoring":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/JobMonitoring","port":9130},"jobStateUpdate":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/JobStateUpdate","port":9136},"matcher":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/Matcher","port":9170},"optimizationMind":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/OptimizationMind","port":9175},"optimizers":{"<<":{"port":null,"replicaCount":1,"type":"executor"},"cmd":"WorkloadManagement/Optimizers","port":null},"pilotManager":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/PilotManager","port":9171},"pilotStatus":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"WorkloadManagement/PilotStatusAgent","port":null},"pilotSync":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"WorkloadManagement/PilotSyncAgent","port":null},"proxyManager":{"<<":{"replicaCount":1,"type":"service"},"cmd":"Framework/ProxyManager","port":9152},"publisher":{"<<":{"replicaCount":1,"type":"service"},"cmd":"ResourceStatus/Publisher","port":9165},"reqExecuting":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"RequestManagement/RequestExecutingAgent","port":null},"reqManager":{"<<":{"replicaCount":1,"type":"service"},"cmd":"RequestManagement/ReqManager","port":9140},"reqProxy":{"<<":{"replicaCount":1,"type":"service"},"cmd":"RequestManagement/ReqProxy","port":9161},"resourceManagement":{"<<":{"replicaCount":1,"type":"service"},"cmd":"ResourceStatus/ResourceManagement","port":9172},"resourceStatus":{"<<":{"replicaCount":1,"type":"service"},"cmd":"ResourceStatus/ResourceStatus","port":9160},"sandboxStore":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/SandboxStore","port":9196},"siteDirector":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"WorkloadManagement/SiteDirector","port":null},"storageElement":{"<<":{"replicaCount":1,"type":"service"},"cmd":"DataManagement/StorageElement","port":9148},"systemAdmin":{"<<":{"replicaCount":1,"type":"service"},"cmd":"Framework/SystemAdministrator","port":9162},"wmsAdmin":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/WMSAdministrator","port":9145}},"diracConfig":{"registry":{"DefaultGroup":"dirac_user","groups":{"dirac_admin":{"properties":["AlarmsManagement","ServiceAdministrator","CSAdministrator","JobAdministrator","FullDelegation","ProxyManagement","Operator"],"users":["dpps_user"]},"dirac_user":{"properties":["NormalUser"],"users":["test_user"]},"dpps_genpilot":{"properties":["GenericPilot","LimitedDelegation"],"users":["dpps_user"]},"dpps_group":{"properties":["NormalUser","PrivateLimitedDelegation"],"users":["dpps_user","test_user"]}},"hosts":null,"users":{"dpps_user":{"CA":"/CN=DPPS Development CA","DN":"/CN=DPPS User"}},"vo":{"ctao.dpps.test":{"DefaultGroup":"dpps_group","IdProvider":"wms-dpps-iam-login-service","VOAdmin":"dpps_user","VOAdminGroup":"dpps_group","VOMSName":"ctao.dpps.test"}}},"resources":{"fileCatalog":"RucioFileCatalog\n{\n  CatalogType = FileCatalog\n  AccessType = Read-Write\n  Status = Active\n  Master = True\n  CatalogURL = DataManagement/FileCatalog\n  MetaCatalog = True\n}\n","sites":"CTAO\n{\n  CTAO.CI.de\n  {\n    Name = CTAO.CI.de\n    CE = dirac-ce\n    CEs\n    {\n      dirac-ce\n      {\n        CEType = SSH\n        SubmissionMode = Direct\n        SSHHost = dirac-ce\n        SSHUser = dirac\n        SSHKey = /home/dirac/.ssh/diracuser_sshkey\n        wnTmpDir = /tmp\n        Pilot = True\n        SharedArea = /home/dirac\n        ExtraPilotOptions = --PollingTime 10 --CVMFS_locations=/\n        Queues\n        {\n          normal\n          {\n            maxCPUTime = 172800\n            SI00 = 2155\n            MaxTotalJobs = 2500\n            MaxWaitingJobs = 300\n            VO = ctao.dpps.test\n            BundleProxy = True\n          }\n        }\n      }\n    }\n  }\n}\n","storageElements":"SandboxSE\n{\n  BackendType = DISET\n  AccessProtocol.1\n  {\n    Host = {{ include \"wms.dirac-service-name\" (dict \"root\" . \"comp\" \"sandboxStore\") }}\n    Port = {{ .Values.diracServer.diracComponents.sandboxStore.port }}\n    PluginName = DIP\n    Protocol = dips\n    Path = /WorkloadManagement/SandboxStore\n    Access = remote\n    WSUrl =\n  }\n}\n"}},"diracDatabases":["AccountingDB","FileCatalogDB","InstalledComponentsDB","JobDB","JobLoggingDB","PilotAgentsDB","ProxyDB","ReqDB","ResourceManagementDB","ResourceStatusDB","SandboxMetadataDB","StorageManagementDB","TaskQueueDB"],"diracx":{"legacyExchangeApiKey":"diracx:legacy:Mr8ostGuB_SsdmcjZb7LPkMkDyp9rNuHX6w1qAqahDg="},"environment":null,"initContainers":{"certKeys":{"volumeMounts":[{"mountPath":"/home/dirac/.ssh","name":"ssh-dir"},{"mountPath":"/opt/dirac/etc/grid-security","name":"certs-dir"},{"mountPath":"/home/dirac/.globus","name":"globus-dir"}],"volumes":[{"emptyDir":{},"name":"ssh-dir"},{"emptyDir":{},"name":"globus-dir"},{"emptyDir":{},"name":"certs-dir"}]}},"masterCS":{"enabled":true,"extraVolumeMounts":null,"extraVolumes":null,"hostkey":{"secretFullName":""},"hostname":"dirac-master-cs","port":9135,"tornado":false},"podAnnotations":{},"podLabels":{},"podSecurityContext":{},"resetDatabasesOnStart":["ResourceStatusDB","ProxyDB","JobDB","SandboxMetadataDB","TaskQueueDB","JobLoggingDB","PilotAgentsDB","ReqDB","AccountingDB","FileCatalogDB","StorageManagementDB"],"securityContext":{},"voName":"ctao.dpps.test","volumeMounts":[],"volumes":[],"webApp":{"enabled":true,"extraVolumeMounts":null,"extraVolumes":null,"hostkey":{"secretFullName":""},"hostname":"dirac-web-app"}}` | Setting for the DIRAC components |
| diracServer.resetDatabasesOnStart | list | `["ResourceStatusDB","ProxyDB","JobDB","SandboxMetadataDB","TaskQueueDB","JobLoggingDB","PilotAgentsDB","ReqDB","AccountingDB","FileCatalogDB","StorageManagementDB"]` | Recreates some DIRAC databases from scratch. Useful at first installation, but destructive on update: should be changed immediately after the first installation. This list might overlap with list of of DBs in chart/templates/configmap.yaml |
| diracx.cert-manager.cainjector.image.repository | string | `"harbor.cta-observatory.org/dpps/quay-io-jetstack-cert-manager-cainjector"` |  |
| diracx.cert-manager.controller.image.repository | string | `"harbor.cta-observatory.org/dpps/quay-io-jetstack-cert-manager-controller"` |  |
| diracx.cert-manager.startupapicheck.image.repository | string | `"harbor.cta-observatory.org/dpps/quay-io-jetstack-cert-manager-ctl"` |  |
| diracx.cert-manager.webhook.image.repository | string | `"harbor.cta-observatory.org/dpps/quay-io-jetstack-cert-manager-webhook"` |  |
| diracx.developer.enabled | bool | `true` |  |
| diracx.developer.localCSPath | string | `"/local_cs_store"` |  |
| diracx.developer.urls.diracx | string | `"http://wms-diracx:8000"` |  |
| diracx.developer.urls.iam | string | `"http://wms-dpps-iam-login-service:8080"` |  |
| diracx.developer.urls.minio | string | `"http://wms-minio:32000"` |  |
| diracx.dex.enabled | bool | `false` |  |
| diracx.diracx.hostname | string | `"wms-diracx"` |  |
| diracx.diracx.osDbs.dbs.JobParametersDB | string | `nil` |  |
| diracx.diracx.settings.DIRACX_CONFIG_BACKEND_URL | string | `"git+file:///cs_store/initialRepo"` |  |
| diracx.diracx.settings.DIRACX_LEGACY_EXCHANGE_HASHED_API_KEY | string | `"19628aa0cb14b69f75b2164f7fda40215be289f6e903d1acf77b54caed61a720"` |  |
| diracx.diracx.settings.DIRACX_SANDBOX_STORE_AUTO_CREATE_BUCKET | string | `"true"` |  |
| diracx.diracx.settings.DIRACX_SANDBOX_STORE_BUCKET_NAME | string | `"sandboxes"` |  |
| diracx.diracx.settings.DIRACX_SANDBOX_STORE_S3_CLIENT_KWARGS | string | `"{\"endpoint_url\": \"http://wms-minio:9000\", \"aws_access_key_id\": \"rootuser\", \"aws_secret_access_key\": \"rootpass123\"}"` |  |
| diracx.diracx.settings.DIRACX_SERVICE_AUTH_ACCESS_TOKEN_EXPIRE_MINUTES | string | `"120"` |  |
| diracx.diracx.settings.DIRACX_SERVICE_AUTH_ALLOWED_REDIRECTS | string | `"[\"http://wms-diracx:8000/api/docs/oauth2-redirect\", \"http://wms-diracx:8000/#authentication-callback\"]"` |  |
| diracx.diracx.settings.DIRACX_SERVICE_AUTH_REFRESH_TOKEN_EXPIRE_MINUTES | string | `"360"` |  |
| diracx.diracx.settings.DIRACX_SERVICE_AUTH_TOKEN_ISSUER | string | `"http://wms-diracx:8000"` |  |
| diracx.diracx.settings.DIRACX_SERVICE_AUTH_TOKEN_KEYSTORE | string | `"file:///keystore/jwks.json"` |  |
| diracx.diracx.sqlDbs.dbs.AuthDB.internalName | string | `"DiracXAuthDB"` |  |
| diracx.diracx.sqlDbs.dbs.JobDB | string | `nil` |  |
| diracx.diracx.sqlDbs.dbs.JobLoggingDB | string | `nil` |  |
| diracx.diracx.sqlDbs.dbs.SandboxMetadataDB | string | `nil` |  |
| diracx.diracx.sqlDbs.dbs.TaskQueueDB | string | `nil` |  |
| diracx.diracx.sqlDbs.default.host | string | `"dirac-db:3306"` |  |
| diracx.diracx.sqlDbs.default.password | string | `"dirac-db"` |  |
| diracx.diracx.sqlDbs.default.rootPassword | string | `"dirac-db-root"` |  |
| diracx.diracx.sqlDbs.default.rootUser | string | `"root"` |  |
| diracx.diracx.sqlDbs.default.user | string | `"Dirac"` |  |
| diracx.diracx.startupProbe.failureThreshold | int | `60` |  |
| diracx.diracx.startupProbe.periodSeconds | int | `15` |  |
| diracx.diracx.startupProbe.timeoutSeconds | int | `5` |  |
| diracx.elasticsearch.enabled | bool | `false` |  |
| diracx.enabled | bool | `true` |  |
| diracx.global.activeDeadlineSeconds | int | `900` |  |
| diracx.global.batchJobTTL | int | `3600` |  |
| diracx.global.imagePullPolicy | string | `"Always"` |  |
| diracx.global.images.busybox.repository | string | `"harbor.cta-observatory.org/proxy_cache/busybox"` |  |
| diracx.global.images.busybox.tag | string | `"latest"` |  |
| diracx.global.images.client | string | `"harbor.cta-observatory.org/dpps/diracgrid-diracx-client"` |  |
| diracx.global.images.services | string | `"harbor.cta-observatory.org/dpps/diracgrid-diracx-services"` |  |
| diracx.global.images.tag | string | `"v0.0.2"` |  |
| diracx.global.images.web.repository | string | `"harbor.cta-observatory.org/dpps/diracgrid-diracx-web-static"` |  |
| diracx.global.images.web.tag | string | `"v0.1.0-a10"` |  |
| diracx.grafana.enabled | bool | `false` |  |
| diracx.indigoiam.enabled | bool | `false` |  |
| diracx.indigoiam.image.repository | string | `"indigoiam/iam-login-service"` |  |
| diracx.indigoiam.image.tag | string | `"v1.13.0-rc2"` |  |
| diracx.initSql.enabled | bool | `false` |  |
| diracx.initSql.env | object | `{}` |  |
| diracx.jaeger.enabled | bool | `false` |  |
| diracx.minio.environment.MINIO_BROWSER_REDIRECT_URL | string | `"http://wms-minio:32001/"` |  |
| diracx.minio.image.repository | string | `"harbor.cta-observatory.org/dpps/quay-io-minio-minio"` |  |
| diracx.minio.image.tag | string | `"RELEASE.2025-09-07T16-13-09Z"` |  |
| diracx.minio.mcImage.repository | string | `"harbor.cta-observatory.org/dpps/quay-io-minio-mc"` |  |
| diracx.minio.mcImage.tag | string | `"RELEASE.2025-08-13T08-35-41Z"` |  |
| diracx.minio.rootPassword | string | `"rootpass123"` |  |
| diracx.minio.rootUser | string | `"rootuser"` |  |
| diracx.mysql.enabled | bool | `false` |  |
| diracx.opensearch.config."opensearch.yml" | string | `"cluster.name: opensearch-cluster\n\n# Bind to all interfaces because we don't know what IP address Docker will assign to us.\nnetwork.host: 0.0.0.0\n\n# Setting network.host to a non-loopback address enables the annoying bootstrap checks. \"Single-node\" mode disables them again.\n# Implicitly done if \".singleNode\" is set to \"true\".\n# discovery.type: single-node\n\n# Start OpenSearch Security Demo Configuration\n# WARNING: revise all the lines below before you go into production\nplugins:\n  security:\n    ssl:\n      transport:\n        pemcert_filepath: hostcert.pem\n        pemkey_filepath: hostkey.pem\n        pemtrustedcas_filepath: ca.pem\n        enforce_hostname_verification: false\n      http:\n        enabled: true\n        pemcert_filepath: hostcert.pem\n        pemkey_filepath: hostkey.pem\n        pemtrustedcas_filepath: ca.pem\n    allow_unsafe_democertificates: true\n    allow_default_init_securityindex: true\n    authcz:\n      admin_dn:\n        - CN=kirk,OU=client,O=client,L=test,C=de\n        - CN={{ include \"certprefix\" . }}-dirac-master-cs\n        - CN={{ include \"certprefix\" . }}-{{ include \"wms.dirac-comp-suffix\" \"wmsAdmin\"}}\n        - CN={{ include \"certprefix\" . }}-{{ include \"wms.dirac-comp-suffix\" \"jobStateUpdate\"}}\n    audit.type: internal_opensearch\n    enable_snapshot_restore_privilege: true\n    check_snapshot_restore_write_privileges: true\n    restapi:\n      roles_enabled: [\"all_access\", \"security_rest_api_access\"]\n    system_indices:\n      enabled: true\n      indices:\n        [\n          \".opendistro-alerting-config\",\n          \".opendistro-alerting-alert*\",\n          \".opendistro-anomaly-results*\",\n          \".opendistro-anomaly-detector*\",\n          \".opendistro-anomaly-checkpoints\",\n          \".opendistro-anomaly-detection-state\",\n          \".opendistro-reports-*\",\n          \".opendistro-notifications-*\",\n          \".opendistro-notebooks\",\n          \".opendistro-asynchronous-search-response*\",\n        ]\n######## End OpenSearch Security Demo Configuration ########\n"` |  |
| diracx.opensearch.enabled | bool | `true` |  |
| diracx.opensearch.extraVolumeMounts[0].mountPath | string | `"/usr/share/opensearch/config/ca.pem"` |  |
| diracx.opensearch.extraVolumeMounts[0].name | string | `"cafile"` |  |
| diracx.opensearch.extraVolumeMounts[0].subPath | string | `"ca.pem"` |  |
| diracx.opensearch.extraVolumeMounts[1].mountPath | string | `"/usr/share/opensearch/config/hostcert.pem"` |  |
| diracx.opensearch.extraVolumeMounts[1].name | string | `"dpps-certkey-600"` |  |
| diracx.opensearch.extraVolumeMounts[1].subPath | string | `"hostcert.pem"` |  |
| diracx.opensearch.extraVolumeMounts[2].mountPath | string | `"/usr/share/opensearch/config/hostkey.pem"` |  |
| diracx.opensearch.extraVolumeMounts[2].name | string | `"dpps-certkey-400"` |  |
| diracx.opensearch.extraVolumeMounts[2].subPath | string | `"hostkey.pem"` |  |
| diracx.opensearch.extraVolumes | string | `"- name: cafile\n  secret:\n    defaultMode: 420\n    secretName: {{ include \"certprefix\" . }}-server-cafile\n- name: dpps-certkey-600\n  secret:\n    defaultMode: 0600\n    secretName: {{ include \"certprefix\" . }}-opensearch-cluster-master-hostkey\n- name: dpps-certkey-400\n  secret:\n    defaultMode: 0400\n    secretName: {{ include \"certprefix\" . }}-opensearch-cluster-master-hostkey\n"` |  |
| diracx.opentelemetry-collector.enabled | bool | `false` |  |
| diracx.prometheus.enabled | bool | `false` |  |
| diracx.rabbitmq.auth.existingErlangSecret | string | `"rabbitmq-secret"` |  |
| diracx.rabbitmq.auth.existingPasswordSecret | string | `"rabbitmq-secret"` |  |
| diracx.rabbitmq.containerSecurityContext.enabled | bool | `false` |  |
| diracx.rabbitmq.enabled | bool | `true` |  |
| diracx.rabbitmq.image.registry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| diracx.rabbitmq.image.repository | string | `"bitnamilegacy/rabbitmq"` |  |
| diracx.rabbitmq.podSecurityContext.enabled | bool | `false` |  |
| diracx_alias_service.enabled | bool | `true` |  |
| diracx_alias_service.name | string | `"wms-diracx"` |  |
| diracx_deployment_fullname | string | `"{{ .Release.Name }}-diracx"` |  |
| fullnameOverride | string | `""` |  |
| global.dockerRegistry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| global.images.busybox.repository | string | `"harbor.cta-observatory.org/proxy_cache/busybox"` |  |
| global.registry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| global.storageClassName | string | `"standard"` |  |
| iam.bootstrap.config.clients[0].client_id | string | `"dpps-test-client"` |  |
| iam.bootstrap.config.clients[0].client_name | string | `"WMS Test Client"` |  |
| iam.bootstrap.config.clients[0].client_secret | string | `"secret"` |  |
| iam.bootstrap.config.clients[0].grant_types[0] | string | `"authorization_code"` |  |
| iam.bootstrap.config.clients[0].grant_types[1] | string | `"password"` |  |
| iam.bootstrap.config.clients[0].grant_types[2] | string | `"client_credentials"` |  |
| iam.bootstrap.config.clients[0].grant_types[3] | string | `"urn:ietf:params:oauth:grant_type:redelegate"` |  |
| iam.bootstrap.config.clients[0].grant_types[4] | string | `"refresh_token"` |  |
| iam.bootstrap.config.clients[0].redirect_uris[0] | string | `"http://wms-diracx:8000/api/auth/device/complete"` |  |
| iam.bootstrap.config.clients[0].redirect_uris[1] | string | `"http://wms-diracx:8000/api/auth/authorize/complete"` |  |
| iam.bootstrap.config.clients[0].scopes[0] | string | `"scim:write"` |  |
| iam.bootstrap.config.clients[0].scopes[1] | string | `"scim:read"` |  |
| iam.bootstrap.config.clients[0].scopes[2] | string | `"offline_access"` |  |
| iam.bootstrap.config.clients[0].scopes[3] | string | `"openid"` |  |
| iam.bootstrap.config.clients[0].scopes[4] | string | `"profile"` |  |
| iam.bootstrap.config.clients[0].scopes[5] | string | `"iam:admin.write"` |  |
| iam.bootstrap.config.clients[0].scopes[6] | string | `"iam:admin.read"` |  |
| iam.bootstrap.config.issuer | string | `"http://wms-dpps-iam-login-service:8080"` |  |
| iam.bootstrap.config.users[0].cert.default_path | string | `"/tmp/usercert.pem"` |  |
| iam.bootstrap.config.users[0].cert.env_var | string | `"X509_USER_CERT"` |  |
| iam.bootstrap.config.users[0].cert.kind | string | `"env_var_file"` |  |
| iam.bootstrap.config.users[0].email | string | `"dpps@test.example"` |  |
| iam.bootstrap.config.users[0].family_name | string | `"User"` |  |
| iam.bootstrap.config.users[0].given_name | string | `"DPPS"` |  |
| iam.bootstrap.config.users[0].groups[0] | string | `"ctao.dpps.test"` |  |
| iam.bootstrap.config.users[0].groups[1] | string | `"dpps_group"` |  |
| iam.bootstrap.config.users[0].groups[2] | string | `"dpps_genpilot"` |  |
| iam.bootstrap.config.users[0].groups[3] | string | `"dirac_admin"` |  |
| iam.bootstrap.config.users[0].groups[4] | string | `"dirac_user"` |  |
| iam.bootstrap.config.users[0].password | string | `"dpps-password"` |  |
| iam.bootstrap.config.users[0].role | string | `"ROLE_USER"` |  |
| iam.bootstrap.config.users[0].subject_dn | string | `"DPPS User"` |  |
| iam.bootstrap.config.users[0].username | string | `"dpps_user"` |  |
| iam.bootstrap.config.users[1].cert.default_path | string | `"/tmp/usercert.pem"` |  |
| iam.bootstrap.config.users[1].cert.env_var | string | `"X509_USER_CERT"` |  |
| iam.bootstrap.config.users[1].cert.kind | string | `"env_var_file"` |  |
| iam.bootstrap.config.users[1].email | string | `"dpps@test.example"` |  |
| iam.bootstrap.config.users[1].family_name | string | `"User"` |  |
| iam.bootstrap.config.users[1].given_name | string | `"TestDpps"` |  |
| iam.bootstrap.config.users[1].groups[0] | string | `"ctao.dpps.test"` |  |
| iam.bootstrap.config.users[1].groups[1] | string | `"dpps_group"` |  |
| iam.bootstrap.config.users[1].groups[2] | string | `"dirac_user"` |  |
| iam.bootstrap.config.users[1].password | string | `"test-password"` |  |
| iam.bootstrap.config.users[1].role | string | `"ROLE_USER"` |  |
| iam.bootstrap.config.users[1].subject_dn | string | `"DPPS User"` |  |
| iam.bootstrap.config.users[1].username | string | `"test_user"` |  |
| iam.bootstrap.config.users[2].email | string | `"dpps@test.example"` |  |
| iam.bootstrap.config.users[2].family_name | string | `"User"` |  |
| iam.bootstrap.config.users[2].given_name | string | `"TestAdmin"` |  |
| iam.bootstrap.config.users[2].groups[0] | string | `"ctao.dpps.test"` |  |
| iam.bootstrap.config.users[2].password | string | `"test-password"` |  |
| iam.bootstrap.config.users[2].role | string | `"ROLE_ADMIN"` |  |
| iam.bootstrap.config.users[2].username | string | `"admin-user"` |  |
| iam.bootstrap.env[0].name | string | `"X509_NON_DPPS_USER_CERT"` |  |
| iam.bootstrap.env[0].value | string | `"/tmp/user-non-dpps-cert.pem"` |  |
| iam.bootstrap.env[1].name | string | `"X509_UNPRIVILEGED_DPPS_USER_CERT"` |  |
| iam.bootstrap.env[1].value | string | `"/tmp/user-unprivileged-cert.pem"` |  |
| iam.bootstrap.extraVolumeMounts | list | `[]` |  |
| iam.bootstrap.extraVolumes | list | `[]` |  |
| iam.bootstrap.image.pullPolicy | string | `"IfNotPresent"` |  |
| iam.bootstrap.image.repository | string | `"harbor.cta-observatory.org/dpps/dpps-iam-client"` |  |
| iam.bootstrap.image.tag | string | `nil` |  |
| iam.bootstrap.tag | string | `nil` |  |
| iam.cert-generator-grid.enabled | bool | `false` |  |
| iam.dev.mount_repo | bool | `false` |  |
| iam.enabled | bool | `true` |  |
| iam.iam.database.external.existingSecret | string | `""` |  |
| iam.iam.database.external.host | string | `"dirac-db"` |  |
| iam.iam.database.external.name | string | `"indigo-iam"` |  |
| iam.iam.database.external.password | string | `"PassW0rd"` |  |
| iam.iam.database.external.port | int | `3306` |  |
| iam.iam.database.external.username | string | `"indigo-iam"` |  |
| iam.iam.fullnameOverride | string | `nil` |  |
| iam.iam.ingress.annotations."nginx.ingress.kubernetes.io/ssl-passthrough" | string | `"true"` |  |
| iam.iam.ingress.annotations."nginx.ingress.kubernetes.io/ssl-redirect" | string | `"true"` |  |
| iam.iam.ingress.className | string | `"nginx"` |  |
| iam.iam.ingress.enabled | bool | `true` |  |
| iam.iam.ingress.tls.enabled | bool | `true` |  |
| iam.iam.ingress.tls.secretName | string | `"wms-tls"` |  |
| iam.iam.loginService.config.java.opts | string | `"-Xms512m -Xmx512m -Djava.security.egd=file:/dev/./urandom -Dspring.profiles.active=prod -Dlogging.level.org.springframework.web=DEBUG -Dlogging.level.com.indigo=DEBUG"` |  |
| iam.iam.mariadb.enabled | bool | `false` |  |
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
| iam_alias_service.enabled | bool | `true` |  |
| iam_alias_service.name | string | `"wms-dpps-iam-login-service"` |  |
| iam_external.enabled | bool | `false` |  |
| image | object | `{"pullPolicy":"IfNotPresent","repository_prefix":"harbor.cta-observatory.org/dpps/wms","tag":null}` | Image settings. |
| image.repository_prefix | string | `"harbor.cta-observatory.org/dpps/wms"` | Prefix of the repository, pods will use <repository_prefix>-{server,client,ce} |
| image.tag | string | `nil` | Image tag, if not set, the chart's appVersion will be used |
| imagePullSecrets | list | `[{"name":"harbor-pull-secret"}]` | Secrets needed to access image registries |
| mariadb | object | `{"auth":{"rootPassword":"dirac-db-root"},"enabled":true,"global":{"security":{"allowInsecureImages":true}},"image":{"registry":"harbor.cta-observatory.org/proxy_cache","repository":"bitnamilegacy/mariadb"},"initdbScripts":{"create-user.sql":"CREATE USER IF NOT EXISTS 'Dirac'@'%' IDENTIFIED BY 'dirac-db';\nCREATE USER IF NOT EXISTS 'indigo-iam'@'%' IDENTIFIED BY 'PassW0rd';\nCREATE DATABASE IF NOT EXISTS `indigo-iam`;\nGRANT ALL PRIVILEGES ON `indigo-iam`.* TO `indigo-iam`@`%`;\nFLUSH PRIVILEGES;\n"}}` | Configuration for the bitnami mariadb subchart. Disable if DIRAC database is provided externally. |
| minio_alias_service.enabled | bool | `true` |  |
| minio_alias_service.name | string | `"wms-minio"` |  |
| nameOverride | string | `""` |  |
| nodeSelector | object | `{}` |  |
| resources | object | `{}` |  |
| rucio.enabled | bool | `false` |  |
| rucio.rucioConfig | string | `nil` |  |
| service.port | int | `8080` |  |
| service.type | string | `"ClusterIP"` |  |
| serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| serviceAccount.automount | bool | `true` | Automatically mount a ServiceAccount's API credentials? |
| serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| serviceAccount.name | string | `""` | If not set and create is true, a name is generated using the fullname template |
| tolerations | list | `[]` |  |
| volumeMounts | list | `[]` |  |
| volumes | list | `[]` |  |
| waitForLoginService.image.pullPolicy | string | `"IfNotPresent"` |  |
| waitForLoginService.image.repository | string | `"almalinux"` |  |
| waitForLoginService.image.tag | int | `9` |  |

