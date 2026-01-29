# src/devopsmind/programs/buildtrack/coverage_rules.py

COVERAGE_RULES = {
    # --------------------------------------------------
    # Execution Design Coverage
    # --------------------------------------------------
    "Linux": [
        "execution/linux",
    ],
    "Git": [
        "execution/git",
    ],
    "Docker": [
        "execution/docker",
    ],

    # --------------------------------------------------
    # Resilience Design Coverage
    # --------------------------------------------------
    "Kubernetes": [
        "resilience/kubernetes",
    ],
    "Helm": [
        "resilience/helm",
    ],

    # --------------------------------------------------
    # Delivery Design Coverage
    # --------------------------------------------------
    "CI/CD": [
        "delivery/cicd",
    ],
    "GitOps": [
        "delivery/gitops",
    ],
}
