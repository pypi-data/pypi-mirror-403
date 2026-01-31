# qualpipe-webapp

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: dev](https://img.shields.io/badge/AppVersion-dev-informational?style=flat-square)

A Helm chart for Qualpipe WebApp with backend and frontend

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| backend.env[0].name | string | `"PYTHONUNBUFFERED"` |  |
| backend.env[0].value | string | `"1"` |  |
| backend.image.pullPolicy | string | `"IfNotPresent"` |  |
| backend.image.repository | string | `"harbor.cta-observatory.org/dpps/qualpipe-webapp-backend"` |  |
| backend.image.tag | string | `""` |  |
| backend.replicaCount | int | `1` |  |
| backend.resources.limits.cpu | string | `"1000m"` |  |
| backend.resources.limits.memory | string | `"1Gi"` |  |
| backend.resources.requests.cpu | string | `"100m"` |  |
| backend.resources.requests.memory | string | `"128Mi"` |  |
| backend.service.port | int | `8000` |  |
| backend.service.targetPort | int | `8000` |  |
| backend.service.type | string | `"ClusterIP"` |  |
| dev.backend.data.hostPath | string | `"data/k8s"` |  |
| dev.backend.editable.enabled | bool | `false` |  |
| dev.backend.editable.path | string | `"src/qualpipe_webapp/backend"` |  |
| dev.frontend.editable.enabled | bool | `false` |  |
| dev.frontend.editable.path | string | `"src/qualpipe_webapp/frontend"` |  |
| frontend.env[0].name | string | `"PYTHONUNBUFFERED"` |  |
| frontend.env[0].value | string | `"1"` |  |
| frontend.image.pullPolicy | string | `"IfNotPresent"` |  |
| frontend.image.repository | string | `"harbor.cta-observatory.org/dpps/qualpipe-webapp-frontend"` |  |
| frontend.image.tag | string | `""` |  |
| frontend.replicaCount | int | `1` |  |
| frontend.resources.limits.cpu | string | `"1000m"` |  |
| frontend.resources.limits.memory | string | `"1Gi"` |  |
| frontend.resources.requests.cpu | string | `"100m"` |  |
| frontend.resources.requests.memory | string | `"128Mi"` |  |
| frontend.service.port | int | `8001` |  |
| frontend.service.targetPort | int | `8001` |  |
| frontend.service.type | string | `"ClusterIP"` |  |
| ingress.annotations | object | `{}` |  |
| ingress.enabled | bool | `true` |  |
| ingress.host | string | `"qualpipe.local"` |  |
| ingress.ingressClassName | string | `nil` |  |

