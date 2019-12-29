# See: https://hub.docker.com/_/python
# See: https://github.com/docker-library/python/blob/ece154e2849e78c383419d0be591cfd332a471d3/3.8/alpine3.12/Dockerfile
##
ARG PYTHON_VERSION=3-alpine
FROM python:${PYTHON_VERSION} as base

# Don't run as root inside container
# TODO: set the User/Group ID to a known value so  it's easier to deal with k8 security context!
##
ARG USER=tmtdt
RUN addgroup -S ${USER} && adduser -S ${USER} -G ${USER}

# Make space for script
##
ARG APP_DIR=/tmtdt
RUN mkdir -p ${APP_DIR}
WORKDIR ${APP_DIR}

# Copy over requirements, install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt



# Now that user/group + dir created w/ base requirements, install the actual app
##
FROM base as app
##
# Arguments that should get passed to build-tool:
# $ docker build <...> --build-arg GIT_COMMIT=$(git log -1 --format=%h) --build-arg GIT_BRANCH=$( git symbolic-ref HEAD --short ) .


ARG GIT_COMMIT=""
ARG GIT_BRANCH=""
ARG VERSION_STRING="${GIT_BRANCH}-${GIT_COMMIT}"
RUN echo "VERSION_STRING is: $VERSION_STRING"

# Copy in the code
COPY tdt ./tdt
# And the sample config file
COPY ./config/config.yaml.sample ./config
# Copy in the launcher
COPY tmtdt.py .

ENTRYPOINT [ "python", "./main.py" ]

# Apply labels
LABEL Author="Karl Quinsland" Version="${VERSION_STRING}"  Name="The Missing Todoist Tools"
LABEL Info="https://github.com/kquinsland/the-missing-todoist-tools"
