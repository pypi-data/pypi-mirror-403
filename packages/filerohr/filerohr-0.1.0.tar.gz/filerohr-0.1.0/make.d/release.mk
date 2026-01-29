.PHONY: release-ready
release-ready:
	@[ -n "$$(git status --porcelain)" ] && echo "working directory must be clean for release" >&2 && exit 1
	true

release-major: BUMP=major
release-minor: BUMP=minor
release-patch: BUMP=patch

.PHONY: release-major release-minor release-patch
release-major release-minor release-patch: release-generic

.PHONY: release-generic
.ONESHELL:
release-generic: release-ready
	$(UV) tool run bump-my-version bump $(BUMP)

help::
	@echo "  release-patch   - create patch release"
	@echo "  release-minor   - create minor release"
	@echo "  release-major   - create major release"
