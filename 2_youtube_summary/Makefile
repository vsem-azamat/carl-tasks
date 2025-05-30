# YouTube Comments Analysis Pipeline Makefile
# Automation for running the comments analysis pipeline

# Set shell for proper color support
SHELL := /bin/bash

# Colors for output (using printf)
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[1;37m
NC := \033[0m

# Directories
SRC_DIR := src
DATA_DIR := data
LOGS_DIR := logs

# Python commands
PYTHON := python3
PIP := pip3

# Detect package manager
define detect_package_manager
	$(eval PKG_MANAGER := $(shell \
		if command -v uv >/dev/null 2>&1; then \
			echo "uv"; \
		elif command -v poetry >/dev/null 2>&1 && [ -f pyproject.toml ]; then \
			echo "poetry"; \
		else \
			echo "pip"; \
		fi))
endef

# Log files
LOG_DOWNLOAD := $(LOGS_DIR)/download.log
LOG_ANALYSIS := $(LOGS_DIR)/analysis.log
LOG_REPORT := $(LOGS_DIR)/report.log

# Default target
.DEFAULT_GOAL := help

.PHONY: help setup clean install run download analyze report status logs clean-cache clean-logs full-clean run-module download-module analyze-module report-module analyze-video-module test-imports

# Show available commands
help:
	@printf "$(CYAN)🚀 YouTube Comments Analysis Pipeline$(NC)\n"
	@printf "\n"
	@printf "$(WHITE)Main commands:$(NC)\n"
	@printf "  $(GREEN)make setup$(NC)       - 📦 Initial project setup (install dependencies)\n"
	@printf "  $(GREEN)make run$(NC)         - 🎯 Run complete pipeline (download → analyze → report)\n"
	@printf "  $(GREEN)make run-module$(NC)  - 🎯 Run complete pipeline using Python modules\n"
	@printf "  $(GREEN)make download$(NC)    - ⬇️  Download comments for all videos\n"
	@printf "  $(GREEN)make analyze$(NC)     - 🔍 Analyze downloaded comments\n"
	@printf "  $(GREEN)make report$(NC)      - 📊 Generate final reports\n"
	@printf "\n"
	@printf "$(WHITE)Modular commands (preferred):$(NC)\n"
	@printf "  $(CYAN)make download-module$(NC) - ⬇️  Download using Python modules\n"
	@printf "  $(CYAN)make analyze-module$(NC)  - 🔍 Analyze using Python modules\n"
	@printf "  $(CYAN)make report-module$(NC)   - 📊 Generate reports using Python modules\n"
	@printf "\n"
	@printf "$(WHITE)Utilities:$(NC)\n"
	@printf "  $(YELLOW)make status$(NC)       - ℹ️  Show data and files status\n"
	@printf "  $(YELLOW)make logs$(NC)         - 📋 Show latest execution logs\n"
	@printf "  $(YELLOW)make test-imports$(NC) - 🧪 Test modular imports\n"
	@printf "  $(YELLOW)make clean$(NC)        - 🧹 Clean temporary files\n"
	@printf "  $(YELLOW)make install$(NC)      - 💾 Reinstall dependencies\n"
	@printf "\n"
	@printf "$(WHITE)Cleanup:$(NC)\n"
	@printf "  $(RED)make clean-cache$(NC)  - 🗑️  Remove analysis cache (recalculate all)\n"
	@printf "  $(RED)make clean-logs$(NC)   - 🗑️  Remove log files\n"
	@printf "  $(RED)make full-clean$(NC)   - ⚠️  Full cleanup (data + cache + logs)\n"

# Initial project setup
setup: create-dirs install
	@printf "$(GREEN)✅ Setup completed!$(NC)\n"
	@printf "$(CYAN)💡 Don't forget to configure config.yaml and set OPENAI_API_KEY$(NC)\n"

# Create necessary directories
create-dirs:
	@printf "$(BLUE)📁 Creating directories...$(NC)\n"
	@mkdir -p $(DATA_DIR)/comments
	@mkdir -p $(DATA_DIR)/analysis
	@mkdir -p $(DATA_DIR)/audience
	@mkdir -p $(LOGS_DIR)

# Install dependencies
install:
	@printf "$(BLUE)📦 Installing dependencies...$(NC)\n"
	$(call detect_package_manager)
	@if [ "$(PKG_MANAGER)" = "uv" ]; then \
		printf "$(CYAN)🚀 Using uv for installation$(NC)\n"; \
		uv pip install -r requirements.txt; \
	elif [ "$(PKG_MANAGER)" = "poetry" ]; then \
		printf "$(PURPLE)📜 Using poetry for installation$(NC)\n"; \
		poetry install; \
	else \
		printf "$(BLUE)🐍 Using pip for installation$(NC)\n"; \
		$(PIP) install -r requirements.txt; \
	fi

# Complete pipeline
run: check-env download analyze report
	@printf "$(GREEN)🎉 Complete analysis finished!$(NC)\n"
	@printf "$(CYAN)📊 Reports ready:$(NC)\n"
	@printf "  - comprehensive_analysis_report.txt\n"
	@printf "  - key_insights_report.txt\n"

# Check environment variables
check-env:
	@printf "$(BLUE)🔍 Checking configuration...$(NC)\n"
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		printf "$(RED)❌ OPENAI_API_KEY not set$(NC)\n"; \
		printf "$(YELLOW)💡 Run: export OPENAI_API_KEY='your-api-key'$(NC)\n"; \
		exit 1; \
	fi
	@if [ ! -f config.yaml ]; then \
		printf "$(RED)❌ config.yaml not found$(NC)\n"; \
		exit 1; \
	fi
	@printf "$(GREEN)✅ Configuration OK$(NC)\n"

# Step 1: Download comments
download: check-env create-dirs
	@printf "$(PURPLE)🔄 Step 1/3: Downloading comments...$(NC)\n"
	@printf "$(BLUE)📝 Logs saved to $(LOG_DOWNLOAD)$(NC)\n"
	@$(PYTHON) -m src.download_comments 2>&1 | tee $(LOG_DOWNLOAD)
	@if [ $$? -eq 0 ]; then \
		printf "$(GREEN)✅ Comments downloaded successfully$(NC)\n"; \
	else \
		printf "$(RED)❌ Error downloading comments$(NC)\n"; \
		printf "$(YELLOW)📋 Check logs: cat $(LOG_DOWNLOAD)$(NC)\n"; \
		exit 1; \
	fi

# Step 2: Analyze comments
analyze: create-dirs
	@printf "$(PURPLE)🔄 Step 2/3: Analyzing comments...$(NC)\n"
	@printf "$(BLUE)📝 Logs saved to $(LOG_ANALYSIS)$(NC)\n"
	@if ! $(PYTHON) -m src.analyze_all 2>&1 | tee $(LOG_ANALYSIS); then \
		printf "$(RED)❌ Error during analysis$(NC)\n"; \
		printf "$(YELLOW)📋 Check logs: cat $(LOG_ANALYSIS)$(NC)\n"; \
		exit 1; \
	fi
	@if [ ! -f "$(DATA_DIR)/aggregated_analysis.json" ]; then \
		printf "$(RED)❌ Analysis did not produce results$(NC)\n"; \
		exit 1; \
	fi
	@printf "$(GREEN)✅ Analysis completed successfully$(NC)\n"

# Step 3: Generate reports
report: create-dirs
	@printf "$(PURPLE)🔄 Step 3/3: Generating reports...$(NC)\n"
	@if [ ! -f "$(DATA_DIR)/aggregated_analysis.json" ]; then \
		printf "$(RED)❌ No analysis data found. Run 'make analyze' first.$(NC)\n"; \
		exit 1; \
	fi
	@printf "$(BLUE)📝 Logs saved to $(LOG_REPORT)$(NC)\n"
	@if ! $(PYTHON) -m src.summarize_results 2>&1 | tee $(LOG_REPORT); then \
		printf "$(RED)❌ Error generating reports$(NC)\n"; \
		printf "$(YELLOW)📋 Check logs: cat $(LOG_REPORT)$(NC)\n"; \
		exit 1; \
	fi
	@printf "$(GREEN)✅ Reports generated successfully$(NC)\n"
	@printf "$(CYAN)📊 Available reports:$(NC)\n"
	@ls -la reports/*.md 2>/dev/null || printf "$(YELLOW)⚠️  Report files not found$(NC)\n"

# Show project status
status:
	@printf "$(CYAN)📊 YouTube Analysis Pipeline Status$(NC)\n"
	@printf "\n"
	@printf "$(WHITE)Configuration:$(NC)\n"
	@if [ -f config.yaml ]; then \
		printf "$(GREEN)✅ config.yaml found$(NC)\n"; \
	else \
		printf "$(RED)❌ config.yaml not found$(NC)\n"; \
	fi
	@if [ -n "$$OPENAI_API_KEY" ]; then \
		printf "$(GREEN)✅ OPENAI_API_KEY set$(NC)\n"; \
	else \
		printf "$(RED)❌ OPENAI_API_KEY not set$(NC)\n"; \
	fi
	@printf "\n"
	@printf "$(WHITE)Data:$(NC)\n"
	@printf "  Downloaded comments: %d files\n" "$$(ls $(DATA_DIR)/comments/*.json 2>/dev/null | wc -l)"
	@printf "  Analysis results: %d files\n" "$$(ls $(DATA_DIR)/analysis/*.json 2>/dev/null | wc -l)"
	@printf "  Final reports: %d files\n" "$$(ls *.txt 2>/dev/null | wc -l)"
	@printf "\n"
	@printf "$(WHITE)Data size:$(NC)\n"
	@du -sh $(DATA_DIR) 2>/dev/null || printf "  Data folder not found\n"

# Show latest logs
logs:
	@printf "$(CYAN)📋 Latest logs$(NC)\n"
	@printf "\n"
	@if [ -f $(LOG_DOWNLOAD) ]; then \
		printf "$(WHITE)🔽 Last lines from download.log:$(NC)\n"; \
		tail -10 $(LOG_DOWNLOAD); \
		printf "\n"; \
	fi
	@if [ -f $(LOG_ANALYSIS) ]; then \
		printf "$(WHITE)🔍 Last lines from analysis.log:$(NC)\n"; \
		tail -10 $(LOG_ANALYSIS); \
		printf "\n"; \
	fi
	@if [ -f $(LOG_REPORT) ]; then \
		printf "$(WHITE)📊 Last lines from report.log:$(NC)\n"; \
		tail -10 $(LOG_REPORT); \
	fi

# Clean temporary files
clean:
	@printf "$(YELLOW)🧹 Cleaning temporary files...$(NC)\n"
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@printf "$(GREEN)✅ Temporary files removed$(NC)\n"

# Clean analysis cache
clean-cache:
	@printf "$(YELLOW)🗑️  Cleaning analysis cache...$(NC)\n"
	@rm -rf $(DATA_DIR)/analysis/*.json
	@printf "$(GREEN)✅ Analysis cache cleared (recalculation required)$(NC)\n"

# Clean logs
clean-logs:
	@printf "$(YELLOW)🗑️  Cleaning logs...$(NC)\n"
	@rm -rf $(LOGS_DIR)/*
	@printf "$(GREEN)✅ Logs cleared$(NC)\n"

# Full cleanup
full-clean: clean clean-cache clean-logs
	@printf "$(YELLOW)🗑️  Full data cleanup...$(NC)\n"
	@rm -rf $(DATA_DIR)/comments/*.json
	@rm -rf *.txt
	@printf "$(GREEN)✅ Full cleanup completed$(NC)\n"

# Modular Python commands (preferred method)
.PHONY: run-module download-module analyze-module report-module analyze-video-module

# Complete pipeline using modules
run-module: check-env download-module analyze-module report-module
	@printf "$(GREEN)🎉 Complete modular analysis finished!$(NC)\n"
	@printf "$(CYAN)📊 Reports ready in reports/ folder$(NC)\n"

# Download using module
download-module: check-env create-dirs
	@printf "$(PURPLE)🔄 Downloading comments (module)...$(NC)\n"
	@$(PYTHON) -m src.download_comments 2>&1 | tee $(LOG_DOWNLOAD)

# Analyze using module  
analyze-module: create-dirs
	@printf "$(PURPLE)🔄 Analyzing comments (module)...$(NC)\n"
	@if ! $(PYTHON) -m src.analyze_all 2>&1 | tee $(LOG_ANALYSIS); then \
		printf "$(RED)❌ Analysis failed$(NC)\n"; \
		exit 1; \
	fi

# Generate reports using module
report-module: create-dirs
	@printf "$(PURPLE)🔄 Generating reports (module)...$(NC)\n"
	@if [ ! -f "$(DATA_DIR)/aggregated_analysis.json" ]; then \
		printf "$(RED)❌ No analysis data found. Run 'make analyze-module' first.$(NC)\n"; \
		exit 1; \
	fi
	@if ! $(PYTHON) -m src.summarize_results 2>&1 | tee $(LOG_REPORT); then \
		printf "$(RED)❌ Report generation failed$(NC)\n"; \
		exit 1; \
	fi
