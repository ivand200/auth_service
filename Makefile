

.PHONY: typehint
typehint:
	mypy --show-error-context --no-strict-optional  $(FILE)

.PHONY: black
black:
	black --check --diff $(FILE)

.PHONY: pylint
pylint:
	pylint $(FILE)

.PHONY: checklist
checklist: typehint black pylint

