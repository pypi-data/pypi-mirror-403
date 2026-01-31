.PHONY: test test-coverage run-docs docs-build docs-gen doc-check doc-sync-preview

# --------------------------------
# Environment Variables
# --------------------------------

PYTHON_VERSION ?= 3.12
VENV_DIR ?= .venv

# --------------------------------
# Development Environment Commands
# --------------------------------

# Create virtual environment with uv using Python 3.12
uv-venv:
	uv venv $(VENV_DIR) --python $(PYTHON_VERSION)
	@echo "Virtual environment created at $(VENV_DIR) with Python $(PYTHON_VERSION)"
	@echo "Run 'source $(VENV_DIR)/bin/activate' to activate"

# Install dependencies with uv
uv-install:
	uv sync --all-extras

# Create venv and install dependencies
uv-setup: uv-venv uv-install
	@echo "Development environment setup complete"

# Remove virtual environment
uv-clean-venv:
	rm -rf $(VENV_DIR)
	@echo "Virtual environment removed"

# --------------------------------
# Testing Commands
# --------------------------------

# Run all tests
test:
	uv run python -m pytest tests/ -v

# Run tests with coverage report
test-coverage:
	uv run python -m pytest tests/ --cov=synapse_sdk --cov-report=term-missing --cov-report=html --cov-report=xml

# --------------------------------
# Documentation Commands
# --------------------------------

# Run Docusaurus Documentation Server for local development
run-docs:
	cd docs && \
		npx docusaurus start --host 0.0.0.0 --port 3500

# Build docs
docs-build:
	cd docs && npm run build

# Generate API docs from Python docstrings
docs-gen:
	uv run pydoc-markdown

# --------------------------------
# Documentation Sync Commands
# --------------------------------

# Check documentation sync status (preview only)
doc-check: doc-sync-preview

# Preview documentation sync issues without making changes
doc-sync-preview:
	@echo "Checking for uncommitted changes..."
	@UNCOMMITTED=$$(git status --short -- '*.py' | wc -l); \
	if [ $$UNCOMMITTED -gt 0 ]; then \
		echo "⚠️  Warning: $$UNCOMMITTED uncommitted Python file(s) found."; \
		echo "This tool only analyzes committed changes."; \
		echo ""; \
		echo "Uncommitted files:"; \
		git status --short -- '*.py'; \
		echo ""; \
		echo "Recommendation: Commit your changes first, then re-run."; \
		echo "  git add . && git commit -m 'your message' && make doc-check"; \
		echo ""; \
		read -p "Continue anyway? (y/N) " -n 1 -r; \
		echo ""; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
			echo "Aborted. Please commit your changes first."; \
			exit 1; \
		fi; \
	fi
	@echo "Analyzing code changes..."
	@PYTHONPATH=. uv run python scripts/doc_sync/analyze.py \
		--base origin/main \
		--head HEAD \
		--output analysis.json
	@echo "Applying documentation rules..."
	@PYTHONPATH=. uv run python scripts/doc_sync/apply_rules.py \
		--input analysis.json \
		--output issues.json \
		--rules .github/doc-sync-rules.yaml
	@echo "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📋 Documentation Sync Analysis"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@cat issues.json | uv run python -c "\
import sys, json; \
data = json.load(sys.stdin); \
summary = data.get('summary', {}); \
issues = data.get('issues', []); \
error_count = summary.get('error', 0); \
warning_count = summary.get('warning', 0); \
info_count = summary.get('info', 0); \
total = error_count + warning_count + info_count; \
print(f'🔴 ERROR:   {error_count}'); \
print(f'🟡 WARNING: {warning_count}'); \
print(f'🔵 INFO:    {info_count}'); \
print(f'📊 Total:   {total}'); \
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'); \
if total == 0: \
    print('✅ No documentation sync issues found.'); \
else: \
    print('Issues found. Use /sync-docs in Claude Code for details and auto-fix.'); \
    if error_count > 0: \
        print(f'⚠️  {error_count} ERROR(s) require immediate attention.');"
	@echo "\nResults saved to: analysis.json, issues.json"
	@echo "To auto-fix issues, use: /sync-docs --auto-fix"
