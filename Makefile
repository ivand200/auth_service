.PHONY: typehint
typehint:
	pytype $(file)

.PHONY: black
black:
	black --diff $(file)

.PHONY: checklist
checklist: typehint black

