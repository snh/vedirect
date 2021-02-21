# -------------------
# The build container
# -------------------
FROM python:3.9-alpine AS build

RUN apk upgrade --no-cache
RUN apk add --no-cache git

COPY . /root/vedirect/

WORKDIR /root/vedirect
RUN python3 setup.py install --user

# -------------------------
# The application container
# -------------------------
FROM python:3.9-alpine

RUN apk upgrade --no-cache
RUN apk add --no-cache tini

COPY --from=build /root/.local /root/.local

ENTRYPOINT ["tini", "--", "/root/.local/bin/vedirect"]
