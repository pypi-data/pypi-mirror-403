{{- define "dpps-iam.client-volume-mounts" -}}
- name: dppsuser-certkey-400
  mountPath: /tmp/userkey.pem
  subPath: dppsuser.key.pem
- name: dppsuser-certkey-600
  mountPath: /tmp/usercert.pem
  subPath: dppsuser.pem
- name: trust-anchors
  mountPath: /etc/grid-security/certificates
  readOnly: true
- name: ca-bundle
  mountPath: /etc/pki
  readOnly: true
- name: vomses
  mountPath: /etc/vomses
  subPath: vomses
- name: vomsdir
  subPath: {{ .Values.iam.vomsAA.config.voName }}
  mountPath: /etc/grid-security/vomsdir/{{ .Values.iam.vomsAA.config.voName }}/voms.test.example.lsc
{{ if .Values.bootstrap.extraVolumeMounts }}
{{- .Values.bootstrap.extraVolumeMounts | toYaml }}
{{- end }}
{{ include "dpps-iam.repo-volume-mount" . }}
{{- end }}


# TODO: use certprefix template?
{{- define "dpps-iam.client-volumes" -}}
- name: dppsuser-certkey
  secret:
    defaultMode: 0420
    secretName: {{ .Release.Name }}-dppsuser-certkey
- name: dppsuser-certkey-600
  secret:
    defaultMode: 0600
    secretName: {{ .Release.Name }}-dppsuser-certkey
- name: dppsuser-certkey-400
  secret:
    defaultMode: 0400
    secretName: {{ .Release.Name }}-dppsuser-certkey
- name: cafile
  secret:
    defaultMode: 0420
    secretName: {{ template "certprefix" . }}-server-cafile
- name: trust-anchors
  persistentVolumeClaim:
    claimName: {{ include "indigo-iam.fullname" . }}-grid-ca-bundle-pvc
- name: ca-bundle
  persistentVolumeClaim:
    claimName: {{ include "indigo-iam.fullname" . }}-ca-bundle-pvc
- name: vomses
  configMap:
    name: {{ include "indigo-iam.fullname" . }}-vomses
- name: vomsdir
  configMap:
    name: {{ include "indigo-iam.fullname" . }}-voms-lsc
{{ if .Values.bootstrap.extraVolumes }}
{{- .Values.bootstrap.extraVolumes | toYaml }}
{{- end }}
{{- include "dpps-iam.repo-volume" . }}
{{- end -}}
