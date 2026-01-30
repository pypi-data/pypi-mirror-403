{{- define "volumes_rucio_config" }}
- name: rucio-config
  configMap:
    name: "{{ include "bdms.rucioConfigMapName" . }}"
{{- end }}
{{- define "volume_mounts_rucio_config" }}
- name: rucio-config
  mountPath: /opt/rucio/etc/rucio.cfg
  subPath: rucio.cfg
- name: rucio-config
  mountPath: /opt/rucio/etc/alembic.ini
  subPath: alembic.ini
{{- end }}
