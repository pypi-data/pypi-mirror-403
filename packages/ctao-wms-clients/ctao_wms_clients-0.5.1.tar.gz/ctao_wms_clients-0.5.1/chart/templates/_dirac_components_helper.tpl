# --- Services ---
## Framework
{{- define "wms.proxyManager.defaultConfig" -}}
Systems
{
  Framework
  {
    Services
    {
      ProxyManager
      {
        MaxThreads = 100
        #Email to use as a sender for the expiration reminder
        MailFrom = "proxymanager@diracgrid.org"
        #Description of rules for access to methods
        Authorization
        {
          Default = authenticated
          getProxy = FullDelegation
          getProxy += LimitedDelegation
          getProxy += PrivateLimitedDelegation
          getVOMSProxy = FullDelegation
          getVOMSProxy += LimitedDelegation
          getVOMSProxy += PrivateLimitedDelegation
          getProxyWithToken = FullDelegation
          getProxyWithToken += LimitedDelegation
          getProxyWithToken += PrivateLimitedDelegation
          getVOMSProxyWithToken = FullDelegation
          getVOMSProxyWithToken += LimitedDelegation
          getVOMSProxyWithToken += PrivateLimitedDelegation
          getLogContents = ProxyManagement
          setPersistency = ProxyManagement
          exchangeProxyForToken = FullDelegation
          exchangeProxyForToken += LimitedDelegation
          exchangeProxyForToken += PrivateLimitedDelegation
        }
        LogLevel = INFO
        Port = {{ $.Values.diracServer.diracComponents.proxyManager.port }}
      }
    }
    URLs
    {
      ProxyManager = {{ include "wms.dipsUrl" (dict "root" $ "svc" "proxyManager") }}
    }
  }
}
{{- end -}}

{{- define "wms.bundleDelivery.defaultConfig" -}}
Systems
{
  Framework
  {
    Services
    {
      BundleDelivery
      {
        Authorization
        {
          Default = authenticated
          FileTransfer
          {
            Default = authenticated
          }
        }
        Port = {{ $.Values.diracServer.diracComponents.bundleDelivery.port }}
      }
    }
    URLs
    {
      BundleDelivery = {{ include "wms.dipsUrl" (dict "root" $ "svc" "bundleDelivery") }}
    }
  }
}
{{- end -}}

{{- define "wms.systemAdmin.defaultConfig" -}}
Systems
{
  Framework
  {
    Services
    {
      SystemAdministrator
      {
        Authorization
        {
          Default = ServiceAdministrator
          storeHostInfo = Operator
        }
        Port = {{ $.Values.diracServer.diracComponents.systemAdmin.port }}
      }
    }
    URLs
    {
      SystemAdministrator = {{ include "wms.dipsUrl" (dict "root" $ "svc" "systemAdmin") }}
    }
  }
}
{{- end -}}

{{- define "wms.componentMonitoring.defaultConfig" -}}
Systems
{
  Framework
  {
    Services
    {
      ComponentMonitoring
      {
        Authorization
        {
          Default = ServiceAdministrator
          componentExists = authenticated
          getComponents = authenticated
          hostExists = authenticated
          getHosts = authenticated
          installationExists = authenticated
          getInstallations = authenticated
          updateLog = Operator
        }
        Port = {{ .Values.diracServer.diracComponents.componentMonitoring.port }}
      }
    }
    URLs
    {
      ComponentMonitoring = {{ include "wms.dipsUrl" (dict "root" . "svc" "componentMonitoring") }}
    }
  }
  Databases
  {
    User = Dirac
    Password = dirac-db
    Host = dirac-db
    Port = 3306
  }
}
{{- end -}}

## WorkloadManagementSystem
{{- define "wms.jobMonitoring.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Services
    {
      JobMonitoring
      {
        Authorization
        {
          Default = authenticated
        }
        Port = {{ .Values.diracServer.diracComponents.jobMonitoring.port }}
      }
    }
      URLs
    {
      JobMonitoring = {{ include "wms.dipsUrl" (dict "root" . "svc" "jobMonitoring") }}
    }
  }
}
{{- end -}}

{{- define "wms.jobManager.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Services
    {
      JobManager
      {
        Authorization
        {
          Default = authenticated
        }
        Port = {{ .Values.diracServer.diracComponents.jobManager.port }}
      }
    }
    URLs
    {
      JobManager = {{ include "wms.dipsUrl" (dict "root" . "svc" "jobManager") }}
    }
  }
}
{{- end -}}

{{- define "wms.jobStateUpdate.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Services
    {
      JobStateUpdate
      {
        MaxThreads = 100
        Authorization
        {
          Default = authenticated
        }
        Port = {{ .Values.diracServer.diracComponents.jobStateUpdate.port }}
      }
    }
    URLs
    {
      JobStateUpdate = {{ include "wms.dipsUrl" (dict "root" . "svc" "jobStateUpdate") }}
    }
  }
}
{{- end -}}

{{- define "wms.matcher.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Services
    {
      Matcher
      {
        MaxThreads = 100
        Authorization
        {
          Default = authenticated
        }
        Port = {{ .Values.diracServer.diracComponents.matcher.port }}
      }
    }
    URLs
    {
      Matcher = {{ include "wms.dipsUrl" (dict "root" . "svc" "matcher") }}
    }
  }
}
{{- end -}}

{{- define "wms.optimizationMind.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Services
    {
      OptimizationMind
      {
        LogLevel = DEBUG
        Port = {{ .Values.diracServer.diracComponents.optimizationMind.port }}
      }
    }
    URLs
    {
      OptimizationMind = {{ include "wms.dipsUrl" (dict "root" . "svc" "optimizationMind") }}
    }
  }
}
{{- end -}}

{{- define "wms.pilotManager.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Services
    {
      PilotManager
      {
        Authorization
        {
          Default = authenticated
        }
        Port = {{ .Values.diracServer.diracComponents.pilotManager.port }}
      }
    }
    URLs
    {
      PilotManager = {{ include "wms.dipsUrl" (dict "root" . "svc" "pilotManager") }}
    }
  }
}
{{- end -}}

{{- define "wms.sandboxStore.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Services
    {
      SandboxStore
      {
        LocalSE = SandboxSE
        MaxThreads = 200
        MaxSandboxSizeMiB = 10
        BasePath = /opt/dirac/storage/sandboxes
        #If true, uploads the sandbox via diracx on an S3 storage
        UseDiracXBackend = True
        Authorization
        {
          Default = authenticated
          FileTransfer
          {
            Default = authenticated
          }
        }
        Port = {{ .Values.diracServer.diracComponents.sandboxStore.port }}
      }
    }
    URLs
    {
      SandboxStore = {{ include "wms.dipsUrl" (dict "root" . "svc" "sandboxStore") }}
    }
  }
}
{{- end -}}

{{- define "wms.wmsAdmin.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Services
    {
      WMSAdministrator
      {
        Authorization
        {
          Default = Operator
          getJobPilotOutput = authenticated
          getSiteMask = authenticated
          getSiteMaskStatus = authenticated
          ping = authenticated
          allowSite = SiteManager
          allowSite += Operator
          banSite = SiteManager
          banSite += Operator
        }
        Port = {{ .Values.diracServer.diracComponents.wmsAdmin.port }}
      }
    }
    URLs
    {
      WMSAdministrator = {{ include "wms.dipsUrl" (dict "root" . "svc" "wmsAdmin") }}
    }
    Databases
    {
      JobParametersDB
      {
        User = admin
        Password = admin
        Host = opensearch-cluster-master
        Port = 9200
        SSL = True
        ca_certs = /etc/grid-security/certificates/dpps_test_ca.pem
      }
    }
  }
}
{{- end -}}

## DataManagement
{{- define "wms.fileCatalog.defaultConfig" -}}
Systems
{
  DataManagement
  {
    Services
    {
      FileCatalog
      {
        UserGroupManager = UserAndGroupManagerDB
        SEManager = SEManagerDB
        SecurityManager = DirectorySecurityManager
        DirectoryManager = DirectoryLevelTree
        FileManager = FileManager
        UniqueGUID = False
        GlobalReadAccess = True
        LFNPFNConvention = Strong
        ResolvePFN = True
        DefaultUmask = 509
        VisibleStatus = AprioriGood
        Authorization
        {
          Default = authenticated
        }
        Port = {{ .Values.diracServer.diracComponents.fileCatalog.port }}
      }
    }
    URLs
    {
      FileCatalog = {{ include "wms.dipsUrl" (dict "root" . "svc" "fileCatalog") }}
    }
  }
}
{{- end -}}

{{- define "wms.storageElement.defaultConfig" -}}
Systems
{
  DataManagement
  {
    Services
    {
      StorageElement
      {
        #Local path where the data is stored
        BasePath = storageElement
        #Port exposed
        Port = 9148
        #Maximum size in MB you allow to store (0 meaning no limits)
        MaxStorageSize = 0
        Authorization
        {
          Default = authenticated
          FileTransfer
          {
            Default = authenticated
          }
        }
        Port = {{ .Values.diracServer.diracComponents.storageElement.port }}
      }
    }
    URLs
    {
      StorageElement = {{ include "wms.dipsUrl" (dict "root" . "svc" "storageElement") }}
    }
  }
}
{{- end -}}

## RequestManagement
{{- define "wms.reqManager.defaultConfig" -}}
Systems
{
  RequestManagement
  {
    Services
    {
      ReqManager
      {
        ConstantRequestDelay = 0
        Authorization
        {
          Default = authenticated
        }
        Port = {{ .Values.diracServer.diracComponents.reqManager.port }}
      }
    }
    URLs
    {
      ReqManager = {{ include "wms.dipsUrl" (dict "root" . "svc" "reqManager") }}
    }
  }
}
{{- end -}}

{{- define "wms.reqProxy.defaultConfig" -}}
Systems
{
  RequestManagement
  {
    Services
    {
      ReqProxy
      {
        SweepSize = 10
        Authorization
        {
          Default = authenticated
        }
        Port = {{ .Values.diracServer.diracComponents.reqProxy.port }}
      }
    }
    URLs
    {
      ReqProxy = {{ include "wms.dipsUrl" (dict "root" . "svc" "reqProxy") }}
    }
  }
}
{{- end -}}

## ResourceStatus
{{- define "wms.resourceStatus.defaultConfig" -}}
Systems
{
  ResourceStatus
  {
    Services
    {
      ResourceStatus
      {
        Authorization
        {
          Default = SiteManager
          select = all
        }
        Port = {{ .Values.diracServer.diracComponents.resourceStatus.port }}
      }
    }
    URLs
    {
      ResourceStatus = {{ include "wms.dipsUrl" (dict "root" . "svc" "resourceStatus") }}
    }
  }
}
{{- end -}}

{{- define "wms.resourceManagement.defaultConfig" -}}
Systems
{
  ResourceStatus
  {
    Services
    {
      ResourceManagement
      {
        Authorization
        {
          Default = SiteManager
          select = all
        }
        Port = {{ .Values.diracServer.diracComponents.resourceManagement.port }}
      }
    }
    URLs
    {
      ResourceManagement = {{ include "wms.dipsUrl" (dict "root" . "svc" "resourceManagement") }}
    }
  }
}
{{- end -}}

{{- define "wms.publisher.defaultConfig" -}}
Systems
{
  ResourceStatus
  {
    Services
    {
      Publisher
      {
        Authorization
        {
          Default = Authenticated
        }
        Port = {{ .Values.diracServer.diracComponents.publisher.port }}
      }
    }
    URLs
    {
      Publisher = {{ include "wms.dipsUrl" (dict "root" . "svc" "publisher") }}
    }
  }
}
{{- end -}}

# --- Agents ---
{{- define "wms.siteDirector.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Agents
    {
      SiteDirector
      {
        Site = CTAO.CI.de
        PollingTime = 10
        PilotDN = /CN=DPPS User
        PilotGroup = dpps_genpilot
        AddPilotsToEmptySites = True
        UpdatePilotStatus = True
        GetPilotOutput = True
        SendPilotAccounting = True
        LogLevel = DEBUG
        PilotDebugMode = True
        GetPilotOutput = True
        MaxJobsInFillMode = 10
      }
    }
  }
}
{{- end -}}

{{- define "wms.reqExecuting.defaultConfig" -}}
Systems
{
  RequestManagement
  {
    Agents
    {
      RequestExecutingAgent
      {
        PollingTime = 60
        RequestsPerCycle = 100
        MinProcess = 20
        MaxProcess = 20
        ProcessPoolQueueSize = 20
        ProcessPoolTimeout = 900
        ProcessPoplStep = 5
        BulkRequest = 0
        OperationHandlers
        {
          ForwardDISET
          {
            Location = DIRAC/RequestManagementSystem/Agent/RequestOperations/ForwardDISET
            LogLevel = INFO
            MaxAttempts = 256
            TimeOut = 120
          }
          ReplicateAndRegister
          {
            Location = DIRAC/DataManagementSystem/Agent/RequestOperations/ReplicateAndRegister
            FTSMode = False
            UseNewFTS3 = True
            FTSBannedGroups = dirac_user
            FTSBannedGroups += lhcb_user
            LogLevel = INFO
            MaxAttempts = 256
            TimeOutPerFile = 600
          }
          PutAndRegister
          {
            Location = DIRAC/DataManagementSystem/Agent/RequestOperations/PutAndRegister
            LogLevel = INFO
            MaxAttempts = 256
            TimeOutPerFile = 600
          }
          RegisterReplica
          {
            Location = DIRAC/DataManagementSystem/Agent/RequestOperations/RegisterReplica
            LogLevel = INFO
            MaxAttempts = 256
            TimeOutPerFile = 120
          }
          RemoveReplica
          {
            Location = DIRAC/DataManagementSystem/Agent/RequestOperations/RemoveReplica
            LogLevel = INFO
            MaxAttempts = 256
            TimeOutPerFile = 120
          }
          RemoveFile
          {
            Location = DIRAC/DataManagementSystem/Agent/RequestOperations/RemoveFile
            LogLevel = INFO
            MaxAttempts = 256
            TimeOutPerFile = 120
          }
          RegisterFile
          {
            Location = DIRAC/DataManagementSystem/Agent/RequestOperations/RegisterFile
            LogLevel = INFO
            MaxAttempts = 256
            TimeOutPerFile = 120
          }
          SetFileStatus
          {
            Location = DIRAC/TransformationSystem/Agent/RequestOperations/SetFileStatus
            LogLevel = INFO
            MaxAttempts = 256
            TimeOutPerFile = 120
          }
        }
      }
    }
  }
}
{{- end -}}

{{- define "wms.pilotStatus.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Agents
    {
      PilotStatusAgent
      {
        PollingTime = 300
        PilotAccountingEnabled = yes
      }
    }
  }
}
{{- end -}}

{{- define "wms.pilotSync.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Agents
    {
      PilotSyncAgent
      {
        PollingTime = 10
        #Directory where the files can be moved. If running on the WebApp, use /opt/dirac/webRoot/www/pilot
        SaveDirectory =  /opt/dirac/webRoot/www/pilot
        #List of locations where to upload the pilot files. Can be https://some.where, or DIRAC SE names.
        # {{ if .Values.diracServer.webApp.enabled }}https://{{ include "wms.fullname" . }}-dirac-web-app:8443/pilot{{ end }}
        UploadLocations =
        #Set to False (or No, or N) to exclude the master CS from the list of CS servers
        IncludeMasterCS = True
      }
    }
  }
}
{{- end -}}

{{- define "wms.cleanReqDB.defaultConfig" -}}
Systems
{
  RequestManagement
  {
    Agents
    {
      CleanReqDBAgent
      {
        PollingTime = 60
        ControlDirectory = control/RequestManagement/CleanReqDBAgent
        #How many days, until finished requests are deleted
        DeleteGraceDays = 60
        #How many requests are deleted per cycle
        DeleteLimit = 100
        #If failed requests are deleted
        DeleteFailed = False
        #How many hours a request can stay assigned
        KickGraceHours = 1
        #How many requests are kicked per cycle
        KickLimit = 10000
        #Number of Days before a Request is cancelled,
        #regardless of State
        #if set to 0 (default) Requests are never cancelled
        CancelGraceDays = 0
      }
    }
  }
}
{{- end -}}

# --- Executors ---
{{- define "wms.optimizers.defaultConfig" -}}
Systems
{
  WorkloadManagement
  {
    Executors
    {
      Optimizers
      {
        Load = JobPath
        Load += JobSanity
        Load += InputData
        Load += JobScheduling
      }
    }
  }
}
{{- end -}}
