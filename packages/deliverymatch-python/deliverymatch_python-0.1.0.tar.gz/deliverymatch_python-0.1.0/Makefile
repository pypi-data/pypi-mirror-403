TMPDIR := $(shell python -c "import tempfile; print(tempfile.gettempdir())")

.PHONY: generate clean install test lint

generate:
ifndef SPEC
	$(error SPEC is required. Usage: make generate SPEC=/path/to/openapi.yaml)
endif
	@echo "Fixing spec..."
	@uv run python openapi/apply-openapi-fixes.py $(SPEC) $(TMPDIR)/openapi-fixed.yaml
	@echo "Generating client..."
	@rm -rf $(TMPDIR)/deliverymatch-generated
	@uv run openapi-python-client generate --path $(TMPDIR)/openapi-fixed.yaml --output-path $(TMPDIR)/deliverymatch-generated --config openapi/config.yaml
	@rm -rf src/deliverymatch
	@cp -r $(TMPDIR)/deliverymatch-generated/deliverymatch src/deliverymatch
	@rm -rf $(TMPDIR)/deliverymatch-generated $(TMPDIR)/openapi-fixed.yaml
	@echo "Done! Client generated in src/deliverymatch"

clean:
	@rm -rf src/deliverymatch

install:
	@uv sync

test:
	@uv run pytest

lint:
	@uv run ruff check src/
