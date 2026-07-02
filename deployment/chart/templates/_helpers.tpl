{{/* Base name of the release. */}}
{{- define "ignite.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Resolve the image tag (defaults to .Chart.AppVersion when not set). */}}
{{- define "ignite.imageTag" -}}
{{- default .Chart.AppVersion .Values.image.tag -}}
{{- end -}}

{{/* Image references per service. */}}
{{- define "ignite.backendImage" -}}
{{- printf "%s/backend:%s" .Values.image.registry (include "ignite.imageTag" .) -}}
{{- end -}}

{{- define "ignite.frontendImage" -}}
{{- printf "%s/frontend:%s" .Values.image.registry (include "ignite.imageTag" .) -}}
{{- end -}}

{{/* Common labels applied to every resource. */}}
{{- define "ignite.labels" -}}
app.kubernetes.io/name: {{ include "ignite.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- with .Values.extraLabels }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{/* Per-component selector labels. Stable across upgrades. */}}
{{- define "ignite.backendSelectorLabels" -}}
app: ignite
component: backend
app.kubernetes.io/name: {{ include "ignite.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "ignite.frontendSelectorLabels" -}}
app: ignite
component: frontend
app.kubernetes.io/name: {{ include "ignite.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
