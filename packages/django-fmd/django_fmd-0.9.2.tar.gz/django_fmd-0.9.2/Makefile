SHELL := /bin/bash

help: ## List all commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9 -_]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

###################################################################################################
# docker

build: ## Update/Build docker services
	mkdir -p volumes/postgresql/data
	./compose.sh pull
	./compose.sh build --pull

up: build ## Start docker containers
	mkdir -p volumes/postgresql/data
	./compose.sh up -d
	$(MAKE) logs

down: ## Stop all containers
	./compose.sh down

shell-django: ## go into a interactive bash shell in Django container
	./compose.sh exec django /bin/bash

run-shell-django: ## Build and start the Django container and go into shell
	./compose.sh build --pull django
	./compose.sh run --entrypoint '/bin/bash' django

logs: ## Display and follow docker logs
	./compose.sh logs --tail=500 --follow

logs-django: ## Display and follow docker logs only from "django" container
	./compose.sh logs --tail=500 --follow django

reload-django: ## Reload the Django dev server
	./compose.sh exec django /django/docker/utils/kill_python.sh
	./compose.sh logs --tail=500 --follow django

logs-caddy: ## Display and follow docker logs only from "caddy" container
	./compose.sh logs --tail=500 --follow caddy

restart-caddy: ## Restart the Caddy container
	./compose.sh restart caddy
	$(MAKE) logs-caddy


restart: down up  ## Restart the containers

.PHONY: help build
