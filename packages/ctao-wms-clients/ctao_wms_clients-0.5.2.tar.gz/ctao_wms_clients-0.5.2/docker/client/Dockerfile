FROM harbor.cta-observatory.org/proxy_cache/almalinux:9

ARG CTADIRAC_VERSION="3.0.11"
ARG USERID=1000
ARG GROUPID=1000

LABEL maintainer="Natthan Pigoux <natthan.pigoux@lupm.in2p3.fr>, Luisa Arrabito <arrabito@in2p3.fr>"
LABEL description="CTADIRAC client docker image"
LABEL org.opencontainers.image.url=https://gitlab.cta-observatory.org/cta-computing/dpps/CTADIRAC

ENV DIRAC_DIR="/home/dirac"
ENV DIRACOS="${DIRAC_DIR}/diracos"

# Needed to clone the dirac-cwl proto
RUN dnf install -y git

RUN \
  if getent group ${GROUPID}; then \
    groupmod --new-name dirac $(getent group ${GROUPID} | cut -d: -f1); \
  else \
    groupadd --gid ${GROUPID} dirac; \
  fi\
  && adduser --uid ${USERID} --gid dirac -s /bin/bash -d /home/dirac dirac

RUN mkdir -p ${DIRAC_DIR} \
    && chown -R dirac:dirac ${DIRAC_DIR}

RUN mkdir -p ${DIRAC_DIR}/.globus \
    && chown -R dirac:dirac ${DIRAC_DIR}/.globus

WORKDIR ${DIRAC_DIR}

# Install DIRAC client
USER dirac

RUN curl -LO https://github.com/DIRACGrid/DIRACOS2/releases/latest/download/DIRACOS-Linux-x86_64.sh \
    && bash DIRACOS-Linux-x86_64.sh -p ${DIRAC_DIR}/diracos \
    && rm -f DIRACOS-Linux-x86_64.sh \
    && source ${DIRAC_DIR}/diracos/diracosrc \
    && pip install --no-cache-dir CTADIRAC==${CTADIRAC_VERSION}

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | sh

ENV \
  PATH="${DIRAC_DIR}/.pixi/bin:$PATH" \
  DIRACX_URL="http://wms-diracx:8000"

# Install dirac-cwl proto
RUN git clone https://github.com/aldbr/dirac-cwl-proto.git \
    && cd dirac-cwl-proto \
    && pixi install

ENV \
  CONDA_PREFIX="${DIRACOS}" \
  MAMBA_ROOT_PREFIX="${DIRACOS}" \
  CONDOR_CONFIG="${DIRACOS}/etc/condor/condor_config" \
  DAVIX_DISABLE_REDIRECT_CACHING=1 \
  DAVIX_USE_LIBCURL=1 \
  GSETTINGS_SCHEMA_DIR="${DIRACOS}/share/glib-2.0/schemas" \
  PATH="${DIRACOS}/bin:${DIRACOS}/condabin:${PATH}" \
  X509_CERT_DIR="${DIRACOS}/etc/grid-security/certificates" \
  X509_VOMSES="${DIRACOS}/etc/grid-security/vomses" \
  X509_VOMS_DIR="${DIRACOS}/etc/grid-security/vomsdir" \
  XML_CATALOG_FILES="file://${DIRACOS}/etc/xml/catalog file:///etc/xml/catalog" \
