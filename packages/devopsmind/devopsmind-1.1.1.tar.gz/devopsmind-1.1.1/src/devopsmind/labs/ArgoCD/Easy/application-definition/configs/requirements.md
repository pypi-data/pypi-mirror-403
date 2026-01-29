# Argo CD Application Requirements

- apiVersion must be argoproj.io/v1alpha1
- kind must be Application
- metadata.name must be defined
- spec must include:
  - source.repoURL
  - source.path
  - destination.server
  - destination.namespace
- syncPolicy must be automated
