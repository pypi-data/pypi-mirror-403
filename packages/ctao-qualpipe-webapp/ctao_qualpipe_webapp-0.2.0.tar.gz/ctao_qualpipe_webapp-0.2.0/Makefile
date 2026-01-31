
.PHONY: dev-forward dev-debug-network dev-trace-request dev-debug-setup kind-status-all

export CHART_NAME=qualpipe-webapp
export CHART_LOCATION=chart

include aiv-toolkit/Makefile

###################
# Debug
###################

# Manual dev-forward, not needed normally, just fallback for debugging
dev-forward:
	@echo "\n⚠️  WARNING: This is not needed with extraPortMappings in kind-dev-config.yml"
	@echo "⚠️  Use this only if extraPortMappings fails or for debugging"
	@echo ""
	@echo "Starting manual port-forward..."
	@echo "Frontend: http://localhost:8080/home"
	@echo "Backend:  http://localhost:8080/api/docs"
	@echo ""
	@echo "Press Ctrl+C to stop"
	kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80

# Debug network topology and connectivity
dev-debug-network:
	echo "\n=== POD IPs ==="; \
	kubectl get pods -n default -o wide; \
	kubectl get pods -n ingress-nginx -o wide; \
	echo ""; \
	echo "=== SERVICE IPs ==="; \
	kubectl get svc -n default; \
	echo ""; \
	echo "=== INGRESS ROUTING ==="; \
	kubectl describe ingress qualpipe-webapp-ingress -n default | grep -A 10 "Rules:"; \
	echo ""; \
	echo "=== TEST CONNECTIVITY ==="; \
	echo "Frontend → Backend (using Python):"; \
	kubectl exec -n default deployment/qualpipe-webapp-frontend -- \
		python3 -c "import httpx; r = httpx.get('http://qualpipe-webapp-backend:8000/api/v1/health', timeout=5); print(f'HTTP {r.status_code}: {r.text}')" 2>/dev/null; \
	echo ""; \
	echo "Ingress → Frontend (using curl from ingress controller):"; \
	kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- \
		curl -s -o /dev/null -w "HTTP %{http_code}\n" http://qualpipe-webapp-frontend.default.svc.cluster.local:8001/health 2>/dev/null; \
	echo ""; \
	echo "Browser → Frontend (via Ingress):"; \
	curl -s -o /dev/null -w "HTTP %{http_code}\n" http://qualpipe.local:8080/health 2>/dev/null; \
	echo "\n✅ Network is correctly set up."

dev-trace-request:
	@echo "\nTracing a request from browser to backend..."
	@echo ""
	@echo "1. Browser → Ingress Controller (localhost:8080)"
	@curl -v http://qualpipe.local:8080/health 2>&1 | grep "< HTTP"
	@echo ""
	@echo "2. Ingress → Frontend Pod"
	@kubectl logs -n ingress-nginx deployment/ingress-nginx-controller --tail=1 | grep qualpipe-webapp-nginx || echo "No recent requests"
	@echo ""
	@echo "3. Frontend Pod logs (last 5 lines):"
	@kubectl logs -n default deployment/qualpipe-webapp-frontend --tail=5
	@echo ""
	@echo "4. Backend Pod logs (last 5 lines):"
	@kubectl logs -n default deployment/qualpipe-webapp-backend --tail=5

dev-debug-setup:
	@echo "\n=== VERIFYING SETUP ==="
	@echo ""
	@echo "1️⃣  Pod IPs:"
	@kubectl get pods -n default -o wide | grep qualpipe-webapp
	@echo ""
	@echo "2️⃣  All Pods in cluster (looking for 10.244.0.7):"
	@kubectl get pods -A -o wide | grep "10.244.0.7" || echo "   No pod with IP 10.244.0.7"
	@echo ""
	@echo "3️⃣  Ingress configuration:"
	@kubectl get ingress qualpipe-webapp-ingress -n default -o yaml | grep -A 20 "spec:" | grep -A 10 "paths:"
	@echo ""
	@echo "4️⃣  Check for multiple Ingress resources:"
	@kubectl get ingress -A
	@echo ""
	@echo "5️⃣  Backend health endpoint test (Backend reachability from Frontend):"
	@kubectl exec -n default deployment/qualpipe-webapp-frontend -- \
		python3 -c "import httpx; r = httpx.get('http://qualpipe-webapp-backend:8000/v1/health'); print(f'Status: {r.status_code}'); print(f'Body: {r.text}')" 2>/dev/null || \
		echo "   ❌ Cannot reach backend /v1/health"
	@echo ""
	@echo "6️⃣ a Frontend health endpoint test (local to frontend):"
	@kubectl exec -n default deployment/qualpipe-webapp-frontend -- \
		python3 -c "import httpx; r = httpx.get('http://127.0.0.1:8001/health'); print(f'Status: {r.status_code}'); print(f'Body: {r.text}')" 2>/dev/null || \
		echo "   ❌ Frontend pod can't serve /health locally"
	@echo ""
	@echo "6️⃣ b Frontend health endpoint test (from backend -> frontend service):"
	@kubectl exec -n default deployment/qualpipe-webapp-backend -- \
		python3 -c "import urllib.request; r = urllib.request.urlopen('http://qualpipe-webapp-frontend:8001/health', timeout=5); print('Status:', r.getcode()); print('Body:', r.read().decode())" 2>&1 || \
		echo "   ❌ Backend cannot reach frontend"
	@echo ""
	@echo "7️⃣  Backend probes configuration:"
	@kubectl get deployment qualpipe-webapp-backend -n default -o yaml | grep -A 5 "livenessProbe\|readinessProbe" || echo "   No probes configured"
	@echo ""
	@echo "8️⃣  Frontend probes configuration:"
	@kubectl get deployment qualpipe-webapp-frontend -n default -o yaml | grep -A 5 "livenessProbe\|readinessProbe" || echo "   No probes configured"
	@echo ""

kind-status-all:
	echo "\n=== STATUS: ==="
	echo "\n=== Kind Cluster ==="
	kind get clusters || echo "No Kind clusters running"
	echo ""
	echo "=== Docker Containers ==="
	docker ps --filter "name=dpps-local" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "No Docker containers running"
	echo ""
	echo "=== Kubernetes Nodes ==="
	kubectl get nodes 2>/dev/null || echo "Cluster node not accessible"
	echo ""
	echo "=== Pods ==="
	kubectl get pods -A 2>/dev/null || echo "Cluster pods not accessible"
	echo ""
	echo "=== Services ==="
	kubectl get svc -A 2>/dev/null || echo "Cluster service not accessible"
	echo ""
	echo "=== Ingress ==="
	kubectl get ingress -A 2>/dev/null || echo "Cluster ingress pods not accessible"
