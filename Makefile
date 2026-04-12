.PHONY: help catalog settings install list plugin refresh

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

catalog: ## Rebuild catalog.json from repo skills
	python scripts/build-catalog.py

settings: ## Generate VS Code chat.agentSkillsLocations snippet
	./scripts/generate-vscode-settings.sh

install: ## Install a skill: make install SKILL=git-commit TARGET=~/.config/skills/
	@if [ -z "$(SKILL)" ] || [ -z "$(TARGET)" ]; then \
		echo "Usage: make install SKILL=<name> TARGET=<dir>"; exit 1; \
	fi
	./scripts/install-skill.sh $(SKILL) $(TARGET)

list: ## List all available skills
	./scripts/install-skill.sh --list

plugin: ## Generate the bundled plugin marketplace files
	python scripts/export-plugin.py

refresh: catalog plugin ## Rebuild catalog and plugin metadata
	@echo "\033[32m✅ Catalog and plugin metadata rebuilt.\033[0m"
