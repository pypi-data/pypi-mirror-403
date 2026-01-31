{{/*
Expand the name of the chart.
*/}}
{{- define "wms.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "wms.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "wms.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "wms.labels" -}}
helm.sh/chart: {{ include "wms.chart" . }}
{{ include "wms.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "wms.selectorLabels" -}}
app.kubernetes.io/name: {{ include "wms.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "wms.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "wms.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{/*
Certificate prefix
*/}}
{{- define "certprefix" -}}
{{- .Release.Name -}}
{{- end -}}

{{/*
Return the master Configuration Server short hostname
*/}}
{{- define "wms.master-short-name" -}}
{{- coalesce .Values.diracServer.masterCS.hostname "dirac-master-cs" -}}
{{- end -}}

{{/*
Return the full hostname of the master Configuration Server
*/}}
{{- define "wms.master-full-name" -}}
{{ include "wms.fullname" .  }}-{{ include "wms.master-short-name" . }}
{{- end -}}

{{/*
Return the master Configuration Server URL
*/}}
{{- define "wms.master-cs-url" -}}
{{- $schema := ternary "https" "dips" .Values.diracServer.masterCS.tornado -}}
{{ $schema }}://{{ include "wms.master-full-name" . }}:{{ .Values.diracServer.masterCS.port }}/Configuration/Server
{{- end -}}


{{/*
Return the DIRAC component with 'dirac-compName' suffix
Usage:
  {{ include "wms.dirac-comp-suffix" "componentName" }}
*/}}
{{- define "wms.dirac-comp-suffix" -}}
{{- $compName := . -}}
{{- printf "dirac-%s" $compName }}
{{- end -}}

{{/*
Return the DIRAC component service name
Usage:
  {{ include "wms.dirac-service-name" (dict "root" . "comp" "componentName") }}
*/}}
{{- define "wms.dirac-service-name" -}}
{{- $root := .root -}}
{{- $compName := .comp -}}
{{ include "wms.fullname" $root }}-{{ include "wms.dirac-comp-suffix" (include "wms.kebab" $compName) }}
{{- end -}}

{{/*
Return the DIRAC component app name
Usage:
  {{ include "wms.dirac-app-name" (dict "root" . "comp" "componentName") }}
*/}}
{{- define "wms.dirac-app-name" -}}
{{- $root := .root -}}
{{- $compName := .comp -}}
{{ include "wms.name" $root }}-{{ include "wms.dirac-comp-suffix" (include "wms.kebab" $compName) }}
{{- end -}}


{{/*
Convert a string to kebab-case
e.g., proxyManager -> proxy-manager
*/}}
{{- define "wms.kebab" -}}
{{- $str := . -}}
{{- $str = regexReplaceAll "([a-z0-9])([A-Z])" $str "${1}-${2}" -}}
{{- $str | lower -}}
{{- end -}}

{{/*
Generate a DIPS URL for a given DIRAC service
Usage:
  {{ include "wms.dipsUrl" (dict "root" . "svc" "wms") }}
*/}}
{{- define "wms.dipsUrl" -}}
{{- $root := .root -}}
{{- $svc := .svc -}}
{{- $svcVal := index $root.Values.diracServer.diracComponents $svc -}}
dips://{{ include "wms.dirac-service-name" (dict "root" $root "comp" $svc) }}:{{ $svcVal.port }}/{{ $svcVal.cmd }}
{{- end -}}

{{/*
Define init container to set up SSH keys for dirac user
Usage:
  {{ include "wms.initContainer.certKeys" . | nindent 6 }}
*/}}
{{- define "wms.initContainer.certKeys" -}}
- name: setup-cert-and-ssh-keys
  image: {{ $.Values.image.repository_prefix }}-server:{{ $.Values.image.tag | default $.Chart.AppVersion }}
  securityContext:
    runAsUser: 0
  command:
    - sh
    - -c
    - |
      set -xe
      mkdir -p /home/dirac/.ssh
      cp -fv /etc/diracuser_sshkey /home/dirac/.ssh/diracuser_sshkey
      cp -fv /etc/diracuser_sshkey.pub /home/dirac/.ssh/diracuser_sshkey.pub
      cp -fv /etc/diracuser_sshkey.pub /home/dirac/.ssh/authorized_keys
      ls -l /home/dirac/.ssh

      mkdir -p /home/dirac/.globus
      cp -fv /globus/usercert.pem /home/dirac/.globus/usercert.pem
      cp -fv /globus/userkey.pem /home/dirac/.globus/userkey.pem

      chown dirac:dirac -R /home/dirac/
      chmod -R u=rwX,go= /home/dirac/.ssh

      cp -fv /etc/grid-security/hostcert.pem /opt/dirac/etc/grid-security/hostcert.pem
      cp -fv /etc/grid-security/hostkey.pem /opt/dirac/etc/grid-security/hostkey.pem

      chmod 600 /opt/dirac/etc/grid-security/hostcert.pem
      chmod 400 /opt/dirac/etc/grid-security/hostkey.pem

      cp -fvr /etc/grid-security/certificates /opt/dirac/etc/grid-security/certificates
      chown -R dirac:dirac /opt/dirac/etc/

      ls -l /opt/dirac/etc
      ls -l /home/dirac/.ssh
      ls -l /home/dirac/.globus

  volumeMounts:
    {{ include "dpps.common-cert-mounts" . | nindent 4 }}
    {{- if .Values.diracServer.initContainers.certKeys.volumeMounts }}
    {{- toYaml .Values.diracServer.initContainers.certKeys.volumeMounts | nindent 4 }}
    {{- end }}
{{- end -}}


{{ define "dpps.common-cert-volumes" }}
- name: cafile
  secret:
    defaultMode: 420
    secretName: {{ include "certprefix" . }}-server-cafile
- name: diracuser-sshkey-600
  secret:
    defaultMode: 0600
    secretName: {{ include "certprefix" . }}-diracuser-sshkey
- name: diracuser-sshkey-644
  secret:
    defaultMode: 0644
    secretName: {{ include "certprefix" . }}-diracuser-sshkey
- name: dppsuser-certkey-600
  secret:
    defaultMode: 0600
    secretName: {{ include "certprefix" . }}-dppsuser-certkey
- name: dppsuser-certkey-400
  secret:
    defaultMode: 0400
    secretName: {{ include "certprefix" . }}-dppsuser-certkey
{{- end }}


{{ define "dpps.common-cert-mounts" }}
- name: cafile
  subPath: ca.pem
  mountPath: /etc/grid-security/certificates/dpps_test_ca.pem
- name: cafile
  subPath: ca.pem
  mountPath: /etc/grid-security/certificates/74df993b.0
- name: cafile
  subPath: dpps_test_ca.crl.r0
  mountPath: /etc/grid-security/certificates/74df993b.r0
- name: cafile
  subPath: dpps_test_ca.crl.r0
  mountPath: /etc/grid-security/certificates/dpps_test_ca.crl.r0
- name: dppsuser-certkey-400
  mountPath: /globus/userkey.pem
  subPath: dppsuser.key.pem
- name: dppsuser-certkey-600
  mountPath: /globus/usercert.pem
  subPath: dppsuser.pem
- name: diracuser-sshkey-600
  subPath: ssh-diracuser_sshkey
  mountPath: /etc/diracuser_sshkey
- name: diracuser-sshkey-644
  subPath: ssh-diracuser_sshkey.pub
  mountPath: /etc/diracuser_sshkey.pub
# host certificates volumes are not defined in the diracServer.volumes
# they must be defined at deployment lvl
- name: dpps-certkey-600
  subPath: hostcert.pem
  mountPath: /etc/grid-security/hostcert.pem
- name: dpps-certkey-400
  subPath: hostkey.pem
  mountPath: /etc/grid-security/hostkey.pem
{{- end }}


# example usage:
# {{ include "dpps.common-hostkey-volumes" (dict "root" . "secretFullName" .Values.diracServer.masterCS.hostkey.secretFullName "suffix" "dirac-master-cs") }}
{{ define "dpps.common-hostkey-volumes" }}
- name: dpps-certkey-600
  secret:
    defaultMode: 0600
    secretName: {{ coalesce .secretFullName (printf "%s-%s-hostkey" .root.Release.Name .suffix)  }}
- name: dpps-certkey-400
  secret:
    defaultMode: 0400
    secretName: {{ coalesce .secretFullName (printf "%s-%s-hostkey" .root.Release.Name .suffix) }}
{{- end }}


{{/*
Return default environment variables for DIRAC
*/}}
{{- define "wms.defaultEnv" -}}
DB_HOSTNAME: {{ .Values.diracDatabases.host }}
DIRAC_CFG_PATH: "/configurations"
DIRAC_CFG_MASTER_CS: "/configurations/masterCS.cfg"
DIRAC_X509_HOST_KEY: "/opt/dirac/etc/grid-security/hostkey.pem"
DIRAC_X509_HOST_CERT: "/opt/dirac/etc/grid-security/hostcert.pem"
X509_CERT_DIR: "/opt/dirac/etc/grid-security/certificates"
X509_VOMS_DIR: "/opt/dirac/etc/grid-security/vomsdir"
X509_VOMSES: "/opt/dirac/etc/grid-security/vomses"
{{- end -}}
