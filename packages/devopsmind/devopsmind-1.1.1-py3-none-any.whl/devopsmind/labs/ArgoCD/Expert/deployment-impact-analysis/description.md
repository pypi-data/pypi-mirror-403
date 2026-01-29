# Analyze GitOps Blast Radius Across Applications

Objective:

Analyze the **blast radius of shared GitOps configuration**
across multiple Argo CD Applications using declarative evidence.

This lab evaluates system-level reasoning expected from
platform and architecture engineers.

Task Requirements:

You are provided with **read-only GitOps artifacts** -

- `manifests/application-a.yaml`
- `manifests/application-b.yaml`
- `manifests/shared-manifest.yaml`
- `manifests/dependency-map.md`

Using only this evidence, complete -

- `impact-analysis.md`

Your analysis must include - 
1. Identification of shared configuration
2. Affected applications
3. Failure propagation explanation
4. One architectural strategy to reduce blast radius

---
Constraints:

- Do NOT deploy or sync using Argo CD
- Do NOT invent dependencies
- Do NOT suggest tooling changes
- Focus on architectural reasoning only
