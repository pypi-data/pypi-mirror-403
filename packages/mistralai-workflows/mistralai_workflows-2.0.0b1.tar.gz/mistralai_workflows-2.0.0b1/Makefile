# See http://go/std-makefile to get an understanding of common Makefile targets used throughout the project

.PHONY: onboarding lint format typecheck test dev installdeps

onboarding:
	@echo "🛠️  Setting up workflow_sdk..."
	@$(MAKE) installdeps
	@echo "✅ workflow_sdk automated onboarding complete. You may still have some manual steps to tackle!"

lint:
	uv run invoke lint

format:
	uv run invoke lint --fix

typecheck:
	uv run invoke typecheck

test:
	uv run invoke tests

dev:
	@echo "Development environment setup"
	@echo "Run 'uv sync' to install dependencies"

installdeps:
	uv sync
