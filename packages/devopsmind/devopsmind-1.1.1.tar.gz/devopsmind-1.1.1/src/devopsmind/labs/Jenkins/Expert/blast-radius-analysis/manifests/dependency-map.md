# CI Dependency Map

- ci-shared-lib
  - Used by: service-a pipeline
  - Used by: service-b pipeline

Change Impact:
- Any failure in ci-shared-lib affects all consuming pipelines
