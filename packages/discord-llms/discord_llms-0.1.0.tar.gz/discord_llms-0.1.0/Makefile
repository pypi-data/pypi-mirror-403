.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck quality test all export

# Colors (ANSI)
YELLOW := \033[33m
GREEN  := \033[32m
BLUE   := \033[34m
RED    := \033[31m
RESET  := \033[0m

# Print helper
PRINT = printf "%b\n"

TAG ?= latest
CONFIG ?= config/config.example.yaml

ifneq ($(filter export,$(MAKECMDGOALS)),)
  ifneq ($(word 2,$(MAKECMDGOALS)),)
    CONFIG := $(word 2,$(MAKECMDGOALS))
    $(eval $(CONFIG):;@:)
  endif
endif

help: ## Show this help message
	@$(PRINT) "$(BLUE)discord-llms Makefile$(RESET)"
	@$(PRINT) ""
	@$(PRINT) "$(YELLOW)Available targets:$(RESET)"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "help"      "Show this help message"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "install"   "Install all dependencies"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "lint"      "Run linters"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "format"    "Run formatters"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "typecheck" "Run typecheckers"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "quality"   "Run code quality checks"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "test"      "Run tests"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "all"       "Run code quality checks and tests"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "export"    "Build Docker image and export tarball"

install: ## Install discord-llms and all dependencies
	@$(PRINT) "$(YELLOW)Installing all dependencies...$(RESET)"
	@uv sync --group dev --group test

lint: ## Run linters
	@$(PRINT) "$(YELLOW)Running Python linter...$(RESET)"
	@uv run ruff check --fix --select I .
	@uv run ruff check --fix .

format: ## Run formatters
	@$(PRINT) "$(YELLOW)Running Python formatter...$(RESET)"
	@uv run ruff check --select I --fix .
	@uv run ruff format .
	@$(PRINT) "$(YELLOW)Running Markdown formatter...$(RESET)"
	@uv run mdformat README.md
	@$(PRINT) "$(YELLOW)Running YAML formatter...$(RESET)"
	@uv run yamlfmt .
	@$(PRINT) "$(YELLOW)Running TOML formatter...$(RESET)"
	@uv run pyproject-fmt -n pyproject.toml

typecheck: ## Run typecheckers
	@$(PRINT) "$(YELLOW)Running Python typechecker...$(RESET)"
	@uv run ty check

quality: lint typecheck format ## Run code quality checks
	@$(PRINT) "$(GREEN)✓ All checks completed$(RESET)"

test: ## Run tests with coverage
	@$(PRINT) "$(YELLOW)Running Python tests with coverage...$(RESET)"
	@uv run pytest --cov=src/discord_llms --cov-report=term-missing --cov-report=html --cov-report=xml

all: lint format typecheck test ## Run code quality checks and tests
	@$(PRINT) "$(GREEN)✓ All checks completed$(RESET)"

export: ## Build Docker image and export a tarball
	@$(PRINT) "$(YELLOW)Building Docker image...$(RESET)"
	@rm -f discord-llms-$(TAG).tar
	@docker build --no-cache --pull --build-arg CONFIG_PATH=$(CONFIG) -t discord-llms:$(TAG) .
	@$(PRINT) "$(YELLOW)Saving Docker image...$(RESET)"
	@docker save -o discord-llms-$(TAG).tar discord-llms:$(TAG)
	@$(PRINT) "$(GREEN)✓ Exported discord-llms-$(TAG).tar$(RESET)"
