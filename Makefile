# Bare bones, for now
##

##
# borrowed from: https://eugene-babichenko.github.io/blog/2019/09/28/nightly-versions-makefiles/
##
# Vars about build state
AG_COMMIT := $(shell git rev-list --abbrev-commit --tags --max-count=1)
TAG := $(shell git describe --abbrev=0 --tags ${TAG_COMMIT} 2>/dev/null || true)
COMMIT := $(shell git rev-parse --short HEAD)
DATE := $(shell git log -1 --format=%cd --date=format:"%Y%m%d")
VERSION := $(TAG:v%=%)

ifneq ($(COMMIT), $(TAG_COMMIT))
	VERSION := $(VERSION)-next-$(COMMIT)-$(DATE)
endif

# Indicate if build done w/ uncommitted files
ifneq ($(shell git status --porcelain),)
	VERSION := $(VERSION)-dirty
endif

FLAGS := "VERSION_STRING=$(VERSION)"

build:
	./version-hook.sh
	docker build --build-arg $(FLAGS) -t tmtdt .

dkr-clean:
	docker image rm tmtdt

run:
	# Two volumes need to be mounted. One for config and the other for jobs
	# Then simply:
	#	make run
	# Assuming that you have a config file and a job file @ the default locations
	##
	docker run -v ${CURDIR}/config:/tmtdt/config:ro -v ${CURDIR}/jobs:/tmtdt/jobs:ro --rm -it tmtdt
