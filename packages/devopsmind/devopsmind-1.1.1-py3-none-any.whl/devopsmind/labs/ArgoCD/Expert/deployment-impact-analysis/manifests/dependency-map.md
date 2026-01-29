# GitOps Dependency Map

Shared Repository: platform.git

- global-config ConfigMap
  - Used by: service-a
  - Used by: service-b

Any change to shared-manifest.yaml affects all consuming applications.
