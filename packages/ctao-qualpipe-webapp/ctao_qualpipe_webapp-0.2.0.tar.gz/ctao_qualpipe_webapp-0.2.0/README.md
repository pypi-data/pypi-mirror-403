# QualPipe-Webapp

<!-- ## 🚀 FastAPI + D3.js QualPipe Dashboard Project -->

The QualPipe-webapp project uses **FastAPI** as backend and frontend, plus **D3.js** for dynamic frontend visualizations, separated into clean services using **Kubernetes (Kind)**.

## Prerequisites

Make sure these software are already installed on your system:
- **Docker** ([Installation Guide](https://docs.docker.com/engine/install/))
- **Pixi** ([Installation Guide](https://pixi.sh/latest/installation/))

<!-- - **Kind** ([Installation Guide](https://kind.sigs.k8s.io/docs/user/quick-start/#installation))
- **kubectl** ([Installation Guide](https://kubernetes.io/docs/tasks/tools/))
- **Helm** ([Installation Guide](https://helm.sh/docs/intro/install/))
- **NodeJS** ([Installation Guide](https://nodejs.org/en/download)) -->

If you are on a Mac, these dependencies can be quickly installed via homebrew executing:

```bash
brew install docker pixi
```

<!-- ```bash
brew install docker kind kubectl helm pixi node
``` -->

and verify the installation

```bash
docker version
pixi -V
```

<!-- ```bash
docker version
kind version
kubectl version --client
helm version
pixi -V
``` -->

## 🚀 Quick Start

### Developer setup (*first time only*)

#### 1. **Clone the repo**:
```bash
git clone <repository-url>
cd qualpipe-webapp
```

#### 2. Setup environment
To setup the development environment execute:
```bash
pixi run dev-setup
```

This will:

- ✅ Create an isolate Python environment with pixi
- ✅ Install all dependencies from pyproject.toml (frontend, test, doc,
   dev)
- ✅ Install the `ctao-qualpipe-webapp` package in editable mode
- ✅ Generate data models
- ✅ Compile backend and frontend requirements
- ✅ Generate javascript schema
- ✅ Install node dependencies

#### 3. Configure host
To add `qualpipe.local` hostname to the `/etc/hosts` file execute:
```bash
echo "127.0.0.1 qualpipe.local" | sudo tee -a /etc/hosts
```

#### 4. Start the local development environment
To deploy the app and start the local development environment execute:
```bash
pixi run dev-up
```

This will:

- ✅ Create a kind cluster with port mappings
- ✅ Build Docker images (backend + frontend)
- ✅ Install NGINX Ingress Controller
- ✅ Deploy the application via Helm

⏳ **Wait** for all pods to be ready (can take 2-3 minutes).

#### 5. Access the application

**No port-forward needed!** The kind cluster exposes ports directly via `extraPortMappings`.

Open in your browser:
- **Frontend**: http://qualpipe.local:8080/home
- **Backend API**: http://qualpipe.local:8080/api/docs

---

### Developer Workflow (*after the first time*)
*Pre-requisite:* the local kubernetes cluster should be running already, if not execute `pixi run dev-up`. If you changed any dependency or modified code that requires model regeneration re-execute `pixi run dev-setup`.

#### If only images are *changed*:
Rebuild images and restart services
```bash
pixi run dev-restart
```

#### If images are *NOT changed*:
Upgrade only Helm chart
```bash
pixi run helm-dev-upgrade
```

#### View logs
To display logs from both *backend* and *frontend* containers execute:
```bash
pixi run kind-logs
```
To stop logs, you can soft-kill them with <kbd>CTRL-C</kbd>.

---

### Verify installation
To check that the app is correctly deployed and properly set up, execute this command:
```bash
pixi run dev-health
```
If something is not ✅ OK check the cluster status with:
```bash
pixi run kind-status
```
or see [Troubleshooting](#%EF%B8%8F-troubleshooting-1).

---

### 🧪 How to run tests
Here below are listed the commands to run all the various possible tests. To get more dertailled information visit also gitlab pages.

#### *Backend unit tests*
```bash
pixi run test-backend
```

#### *Frontend python unit tests*
```bash
pixi run test-frontend-py
```

#### *Frontend javascript unit tests*
```bash
pixi run test-frontend-js
```

#### *Frontend end-to-end tests*
By default the installed test browser are `chromium`, `firefox`, and `webkit` (Safari). Other browsers can be installed modifying the file `playwright.config.ts`. To execute the test run:

```bash
pixi run test-frontend-e2e
```

If the tests are failing for some browsers you can restrict the tests to a specific browser, e.g. Chromium, adding the flag `--project=chromium`  to the above command. See also the [troubleshooting](#%EF%B8%8F-troubleshooting-1).

To inspect the interactive html generated report simply execute:
```bash
npx playwright show-report
```
This will serve the interactvie html report at http://localhost:9323. Press <kbd>Ctrl+C</kbd> to quit.

#### *All tests*
To run all kinds of tests execute:
```bash
pixi run all-tests
```

You can always add the flag `--project=chromium` (or `firefox` or `webkit`) at the end of the previous command.

---

### Cleanup
When you have done with your development you can execute a [soft clean](#soft-clean) or a [full clean](#full-clean)

#### Soft clean
To stop only the pods, preserving the cluster, simply execute:
```bash
pixi run stop
```

To restart your development workflow then execute one of the following command, upon your case:
```bash
# With images rebuilding
pixi run dev-restart
# Without images rebuilding
pixi run dev-restart-no-build
```

#### Full clean
To stop the pods and remove the cluster execute:
```bash
pixi run stop-and-delete
```

To restart you development workflow, if you did not change the image, then execute:
```bash
pixi run dev-up-no-build
```

Otherwise if you need also to rebuild the image restart it with:
```bash
pixi run dev-up
```

#### Docker clean
You can remove the unused Docker container with:
```bash
pixi run prune
```

If you instead you want to clean everything (stop pods, remove cluster, remove docker images) you can execute:
```bash
pixi run clean-all
```

To restart your development workflow you can execute:
```bash
pixi run dev-up
```

---

## 📂 Project Structure

```bash
/qualpipe-webapp
│
├── kind-dev-config.yml              # Kind configuration file for local development
├── chart/                           # Helm chart instructions for deployment
├── Makefile                         # Makefile to build Backend and Frontend
│
├── docs/                            # Document folder
│
├── src/
│   └── qualpipe_webapp/
│       ├── backend/                 # FastAPI backend
│       │   ├── main.py              # Main FastAPI app for backend
│       │   ├── data/                # JSON data sources
│       │   ├── requirements.txt     # Backend dependencies
│       │   ├── requirements-dev.txt # Backend dependencies for developer
│       │   └── Dockerfile           # Backend container
│       │
│       ├── frontend/                # FastAPI frontend
│       │   ├── /templates/          # Template pages
│       │   ├── /static/             # Static files (css, js, lib)
│       │   ├── main.py              # Main FastAPI app for frontend
│       │   ├── requirements.txt     # Frontend dependencies
│       │   ├── requirements-dev.txt # Frontend dependencies for developer
│       │   └── Dockerfile           # Frontend container
│       │
│       ├── nginx/
│       │   ├── nginx.conf
│       │   └── ssl/                 # (optional later)
│      ...
└── .gitignore
```

## Pixi command
All the available Pixi tasks are listed and described in the table below.

| Command: `pixi` | Description |
|---------|-------------|
| `shell` | Activate the pixi environment |
| `run install` | Install editable pixi environment |
| `run install-all` | Install editable pixi environment with all extra dependencies |
| `run compile-requirements-backend` | Generate/update backend requirements.txt|
| `run compile-requirements-frontend` | Generate/update frontend requirements.txt|
| `run compile-requirements-backend-dev` | Generate/update backend requirements-dev.txt|
| `run compile-requirements-frontend-dev` | Generate/update frontend requirements-dev.txt|
| `run compile-requirements` | Generate/update backend and frontend requirements.txt|
| `run compile-requirements-dev` | Generate/update backend and frontend requirements-dev.txt|
| `run npm-install` | Install NodeJS dependencies |
| `run generate-codegen` | Generate Pydantic models from qualpipe criteria |
| `run generate-frontend-schema` | Generate yaml file for javascript frontend validation (combines those produced by `generate-codegen`) |
| `run build-backend` | Build backend image |
| `run build-backend-dev` | Build backend dev image |
| `run build-frontend` | Build frontend image |
| `run build-frontend-dev` | Build frontend dev image |
| `run build-images` | Build backend- and frontend- images |
| `run build-images-dev` | Build backend- and frontend- dev images |
| `run kind-create` | Create local kind cluster |
| `run kind-delete` | Delete local kind cluster |
| `run kind-load-images` | Load docker images on the cluster |
| `run kind-load-dev-images` | Load docker dev images on the cluster |
| `run kind-status` | Show kubernetes cluster status |
| `run kind-clean-failed` | Remove kubernetes resources left from previously failed installation |
| `run helm-install` | Install Helm chart |
| `run helm-dev-install` | Install Helm chart for local development |
| `run helm-uninstall` | Uninstall Helm chart|
| `run helm-upgrade` | Upgrade Helm chart |
| `run helm-dev-upgrade` | Upgrade Helm chart for local development |
| `run ingress-install` | Install NGINX ingress controller for kind |
| `run setup` | Install dependencies, execute ``generate-codegen`` and ``generate-frontend-schema``, and install nodejs dependencies |
| `run dev-setup` | Install dev dependencies in editable mode, execute ``generate-codegen`` and ``generate-frontend-schema``, and install nodejs dependencies |
| `run up` | Production deployment |
| `run dev-up` | Deploy the complete development environment (create a kubernetes cluster, build docker dev images, install NGINX ingress controller for kind, install dev helm chart) |
| `run dev-up-no-build` | Deploy the complete development environment without rebuilding images |
| `run restart` | Build images and reinstall Helm chart |
| `run dev-restart` | Build dev images and reinstall Helm chart |
| `run dev-restart-no-build` | Reinstall Helm chart |
| `run stop` | Stop pods preserving cluster |
| `run stop-and-delete` | Stop pods and delete the cluster |
| `run prune` | Cleanup dangling Docker images |
| `run clean-all` | Stop pods, delete cluster, and remove docker images |
| `run browser-install` | Install Playwright browsers for e2e tests |
| `run test-backend` | Run backend python unit tests |
| `run test-frontend-py` | Run frontend python unit tests |
| `run test-frontend-js` | Run frontend javascript unit tests with Mocha |
| `run test-frontend-e2e` | Run frontend javascript end-to-end tests with Playwright |
| `run all-tests` | Run all backend and frontend tests |
| `run check-backend` | Check backend health |
| `run check-frontend` | Check frontend health |
| `run check` | Check backend and frontend health |
| `run kind-logs-backend` | Show backend container logs |
| `run kind-logs-frontend` | Show frontend container logs|
| `run kind-logs` | Show backend and frontend container logs|
| `run dev-health` | Check backend and frontend health, check API endpoint, check that pods are running |
| `run format` | Run ruff formatting |
| `run lint` | Run ruff linting |
| `run lint-fix` | Run ruff linting and fix |

### Pixi dependency graph tasks
```bash
install ─┐
         │
generate-codegen ─┐
                  │
compile-requirements-backend ──┐
                               ├─→ compile-requirements
compile-requirements-frontend ─┘

compile-requirements-backend-dev ──┐
                                   ├─→ compile-requirements-dev
compile-requirements-frontend-dev ─┘

install-all ─┐
             │
generate-codegen ─┐
                  │
compile-requirements-backend-dev ──┐
                                   ├─→ compile-requirements-dev
compile-requirements-frontend-dev ─┘           │
                                               │
npm-install ───────────────────────────────────┤
                                               ├─→ dev-setup
generate-frontend-schema ──────────────────────┘


kind-create ───────────────────────────────────┐
build-backend-dev  ─────────────┐              │
                                ├─→ build-images-dev ─┐
build-frontend-dev ─────────────┘                     │
                                                      ├─→ dev-up
ingress-install ──────────────────────────────────────┤
helm-dev-install ─────────────────────────────────────┘

kind-create ───────┐
ingress-install ───├─→ dev-up-no-build
helm-dev-install ──┘

build-backend ──┐
                ├─→ build-images
build-frontend ─┘

kind-clean-failed ─┐
                   ├─→ helm-install
kind-load-images ──┘

kind-clean-failed ────┐
                      ├─→ helm-dev-install
kind-load-dev-images ─┘

kind-load-images ──→ helm-upgrade
kind-load-dev-images ──→ helm-dev-upgrade

helm-uninstall ───┐
build-images ─────┤─→ restart
helm-install ─────┘

helm-uninstall ───┐
build-images-dev ─┤─→ dev-restart
helm-install ─────┘

helm-uninstall ───┐
                  ├─→ dev-restart-no-build
helm-dev-install ─┘

helm-uninstall ──→ stop

kind-delete ─┐
             ├─→ stop-and-delete
             └─→ clean-all

test-backend ──────────────┐
test-frontend-py ──────────┤
test-frontend-js ──────────┤
browser-install ──→ test-frontend-e2e
                           └─→ all-tests

check-backend ──┐
                ├─→ check
check-frontend ─┘

kind-logs-backend ──┐
                    ├─→ kind-logs
kind-logs-frontend ─┘
```

## Makefile commands for advanced debug

We use the Makefile only for advanced debug pourposes

| Makefile command         | Description                                   |
|--------------------------|-----------------------------------------------|
| `make dev-forward`       | Manual port-forward (debug/fallback)          |
| `make dev-debug-network` | Debug network cluster/pod/ingress             |
| `make dev-trace-request` | Trace end-to-end request                      |
| `make dev-debug-setup`   | Advance diagnostic cluster setup              |
| `make kind-status-all`   | Complete health check cluster/app             |

### Code Generation Workflow

The project automatically generates Pydantic models from qualpipe criteria classes:

```bash
# Generate models manually
pixi run generate-codegen

# Or use the console script directly (after installation)
qualpipe-generate-models --module qualpipe.core.criterion \
    --out-generated src/qualpipe_webapp/backend/generated \
    --out-schemas src/qualpipe_webapp/frontend/static
```

The code generation creates:

- **Python Models**: `src/qualpipe_webapp/backend/generated/qualpipe_criterion_model.py`
  - Pydantic models for each criterion type
  - Validation logic for telescope parameters
  - Type-safe configuration classes

- **JSON/YAML Schemas**: `src/qualpipe_webapp/frontend/static/`
  - `criteria_schema.json` - JSON schema for frontend criteria report validation
  - `criteria_schema.yaml` - YAML schema for configuration

Such files are then implemented into `metadata_schema.yaml` with:

```bash
pixi run generate-frontend-schema
```

which is used for complete frontend validations, with all the correct references read from the configuration file `config.js`. The `metadata_schema.yaml` file is auto-generated from a template, so

> [!IMPORTANT]
> Do not edit `metadata_schema.yaml` directly — edit `template_metadata_schema.yaml` instead.

### Integration with CI/CD

The generated models are automatically created during:
- **Local development**: `pixi run dev-setup`
- **CI/CD pipelines**: Code generation runs before CI tests
- **Package installation**: Post-install hooks generate models

> [!IMPORTANT] Important Notes
> ⚠️ **Generated files are git-ignored** - They're created automatically and should not be committed.
>
> ✅ **Some tests depend on generated models** - Always run code generation before testing, if your changes had an impact on the models.
>
> 🔄 **Automatic regeneration** - Models update automatically when qualpipe criteria change.

### 🛠️ Troubleshooting

> [!IMPORTANT] Import errors with generated models?
> ```bash
> pixi run generate-codegen  # Regenerate models
> ```

<a id="tests-failing"></a>
> [!IMPORTANT] Tests failing?
> ```bash
> # Ensure models and schemas are generated before running tests
> pixi run generate-codegen
> pixi run generate-frontend-schema
> pixi run test
> ```

> [!IMPORTANT] Pixi environment issues?
> ```bash
> pixi clean              # Clean cache
> pixi run dev-setup      # Complete reinstall + code generation
> ```

> [!IMPORTANT] Port already in use
> If you see errors like `bind: address already in use`:
> ```bash
> # Find process using port 8080
> lsof -i :8080
>
> # Kill the process
> kill -9 <PID>
>
> # Or delete and recreate cluster
> make kind-delete
> make dev-up
> ```

> [!IMPORTANT] Application not accessible
> To use the cluster run 'make export-kubeconfig'
> 1. **Check if pods are running:**
>    ```bash
>    kubectl get pods -n default
>    ```
>    All pods should be `Running` with `READY 1/1`.
>
> 2. **Check Ingress:**
>    ```bash
>    kubectl get ingress -n default
>    kubectl describe ingress qualpipe-webapp-ingress -n default
>    ```
>
> 3. **Check Ingress Controller:**
>    ```bash
>    kubectl get pods -n ingress-nginx
>    ```
>    The `ingress-nginx-controller-*` pod should have STATUS: `Running`.
>
> 4. **Manual port-forward (fallback):**
>    Try to setup a manual port forward with:
>    ```bash
>    make dev-forward
>    ```
>    Then try to access: http://localhost:8080/

> [!IMPORTANT] Logs not showing
> Inspect last logs with:
> ```bash
> # Backend logs
> kubectl logs -n default -l app.kubernetes.io/component=backend --tail=50
>
> # Frontend logs
> kubectl logs -n default -l app.kubernetes.io/component=frontend --tail=50
>
> # Nginx logs
> kubectl logs -n default -l app.kubernetes.io/component=nginx --tail=50
>
> # Ingress Controller logs
> kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50
> ```

> [!IMPORTANT] Playwright test are failing for a specific browser?
> You can execute Playwright tests on a specific browser (chromium, firefox, webkit)
>
>```bash
>npx playwright test --project=chromium
>```
>
>⚠️ **Note:** WebKit browser generally works only with the latest Mac OS update.

> [!IMPORTANT] Some tests about validation are failing?
> Ensure you have generated models and schema (see the [Tests failing?](#tests-failing) section for detailed instructions.)

> [!IMPORTANT] All test failing with ERR_CONNECTION_REFUSED?
> Verify that the WebApp is running, executing
>
>
> Or you can open a browser and navigate to http://qualpipe.local:8080/home . If you can't display the page, the WebApp is not running. See instruction above on how to run it.

---

## 👩‍💻 Contributing

If you want to contribute in developing the code, be aware that we are using `pre-commit`, `code-spell` and `ruff` tools for automatic adherence to the code style. To enforce running these tools whenever you make a commit, setup the [`pre-commit hook`][pre-commit] executing:

```
pre-commit install
```

The `pre-commit hook` will then execute the tools with the same settings as when a merge request is checked on GitLab, and if any problems are reported the commit will be rejected. You then have to fix the reported issues before tying to commit again.

## 📄 License

This project is licensed under the BSD 3-Clause License. See the LICENSE file for details.

[pre-commit]:https://pre-commit.com/

---

## Useful Links

- [pre-commit documentation](https://pre-commit.com/)
- [Mocha documentation](https://mochajs.org/)
- [Playwright documentation](https://playwright.dev/)
- [Pytest documentation](https://docs.pytest.org/)
