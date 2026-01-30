"""
Constants and configuration values for GitLab CI/CD Migration system.
"""

# Version information
VERSION = "1.0.0"

# Default file names
DEFAULT_CONFIG_FILE = "ci-config.yaml"
DEFAULT_OUTPUT_FILE = ".gitlab-ci.yml"
DEFAULT_SCHEMA_FILE = "schemas/ci-config.schema.json"

# Default directories
DEFAULT_HELM_OUTPUT_DIR = "/tmp/helm-charts"
DEFAULT_K8S_CHARTS_DIR = "/tmp/k8s-charts"
DEFAULT_CHANGE_DETECTION_FILE = "changed-components.json"

# GitLab CI/CD constants
GITLAB_CI_VERSION = "1.0"
DEFAULT_DOCKER_IMAGE = "docker:24.0.5"
DEFAULT_KUBECTL_IMAGE = "bitnami/kubectl:1.28"
DEFAULT_HELM_IMAGE = "alpine/helm:3.13.0"
DEFAULT_SONAR_IMAGE = "sonarsource/sonar-scanner-cli:5.0"

# Stage names
STAGE_VALIDATE = "validate"
STAGE_CHANGE_DETECTION = "change-detection"
STAGE_BUILD = "build"
STAGE_PUBLISH = "publish"
STAGE_QUALITY = "quality"
STAGE_DEPLOY = "deploy"

# Default branch patterns per environment
DEFAULT_BRANCH_PATTERNS = {
    "dev": ["develop", "develop-*"],
    "stg": ["staging", "stage", "stg"],
    "ese": ["main", "master", "production"],
}

# Default comparison branches per environment
DEFAULT_COMPARE_BRANCHES = {
    "dev": None,  # Always build in dev
    "stg": "develop",
    "ese": "staging",
}

# Registry types
REGISTRY_TYPE_DOCKER = "docker"  # Generic Docker Registry V2 API (Nexus, Harbor, GitLab, etc.)
REGISTRY_TYPE_ECR = "ecr"
REGISTRY_TYPE_DOCKERHUB = "dockerhub"

# Component types
COMPONENT_TYPE_VUE = "vue"
COMPONENT_TYPE_NPM = "npm"
COMPONENT_TYPE_MAVEN = "maven"
COMPONENT_TYPE_GRADLE = "gradle"
COMPONENT_TYPE_PYTHON = "python"

# Artifact types
ARTIFACT_TYPE_DOCKER = "docker"
ARTIFACT_TYPE_JAR = "jar"
ARTIFACT_TYPE_NPM = "npm"
ARTIFACT_TYPE_WHEEL = "wheel"

# Deploy methods
DEPLOY_METHOD_KUBERNETES = "kubernetes"
DEPLOY_METHOD_DOCKER_COMPOSE = "docker-compose"

# Quality gate operators
OPERATOR_GT = "GT"
OPERATOR_LT = "LT"
OPERATOR_EQ = "EQ"
OPERATOR_GTE = "GTE"
OPERATOR_LTE = "LTE"

# Kubernetes resource types
K8S_RESOURCE_DEPLOYMENT = "deployment"
K8S_RESOURCE_SERVICE = "service"
K8S_RESOURCE_INGRESS = "ingress"
K8S_RESOURCE_CONFIGMAP = "configmap"
K8S_RESOURCE_SECRET = "secret"
K8S_RESOURCE_HPA = "horizontalpodautoscaler"

# Probe types
PROBE_TYPE_HTTP = "httpGet"
PROBE_TYPE_EXEC = "exec"
PROBE_TYPE_TCP = "tcpSocket"

# Default probe configurations
DEFAULT_LIVENESS_PROBE = {
    "httpGet": {
        "path": "/health",
        "port": 8080,
    },
    "initialDelaySeconds": 30,
    "periodSeconds": 10,
}

DEFAULT_READINESS_PROBE = {
    "httpGet": {
        "path": "/ready",
        "port": 8080,
    },
    "initialDelaySeconds": 10,
    "periodSeconds": 5,
}

# Retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2
RETRY_INITIAL_DELAY = 1

# Timeout configuration (in seconds)
DOCKER_BUILD_TIMEOUT = 1800  # 30 minutes
DOCKER_PUSH_TIMEOUT = 900    # 15 minutes
KUBECTL_TIMEOUT = 300        # 5 minutes
GIT_CLONE_TIMEOUT = 300      # 5 minutes
SONAR_SCAN_TIMEOUT = 1800    # 30 minutes

# File patterns
SSL_CERT_PATTERNS = ["*.crt", "*.pem"]
SSL_KEY_PATTERNS = ["*.key"]
CONFIGMAP_FILE_PATTERNS = ["nginx.conf", "conf.properties", "*.json"]

# ArgoCD constants
ARGOCD_API_VERSION = "argoproj.io/v1alpha1"
ARGOCD_APPLICATION_KIND = "Application"
ARGOCD_DEFAULT_PROJECT = "default"

# Helm constants
HELM_API_VERSION = "v2"
HELM_CHART_TYPE = "application"
HELM_DEFAULT_APP_VERSION = "1.0.0"
