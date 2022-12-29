.PHONY: typehint
typehint:
	pytype $(file)

.PHONY: black
black:
	black --diff $(file)

.PHONY: checklist
checklist: typehint black

.PHONY: rabbit
rabbit:
	sudo docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.11-management
