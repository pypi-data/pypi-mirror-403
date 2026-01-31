FROM harbor.cta-observatory.org/proxy_cache/almalinux:9

ARG DIRACOS_VERSION="2.54"
ARG CTADIRAC_VERSION="3.0.11"
ARG RUCIO_VERSION="38.2.0"
ARG RUCIO_POLICY_VERSION="0.2.0"
ARG USERID=1000
ARG GROUPID=1000

RUN dnf install -y \
  procps-ng \
  psmisc \
  openssh-clients \
  iptables-services

RUN \
  if getent group ${GROUPID}; then \
    groupmod --new-name dirac $(getent group ${GROUPID} | cut -d: -f1); \
  else \
    groupadd --gid ${GROUPID} dirac; \
  fi\
  && adduser --uid ${USERID} --gid dirac -s /bin/bash -d /home/dirac dirac

RUN mkdir -p /opt/dirac/etc/grid-security/certificates /etc/grid-security/certificates \
  && chown -R dirac:dirac /opt/dirac /etc/grid-security

# run everything here as dirac user to get correct permissions
USER dirac


# install diracos and CTADIRAC
WORKDIR /home/dirac
ENV DIRAC_ROOT_PATH=/opt/dirac
ENV DIRACOS="${DIRAC_ROOT_PATH}/diracos"

RUN \
  curl -sSfLO "https://github.com/DIRACGrid/DIRACOS2/releases/download/${DIRACOS_VERSION}/DIRACOS-Linux-x86_64.sh" \
  && bash "DIRACOS-Linux-x86_64.sh" -p ${DIRACOS} \
  && rm "DIRACOS-Linux-x86_64.sh" \
  && source "${DIRACOS}/diracosrc" \
  && micromamba clean --all --yes \
  && pip install --no-cache-dir \
    CTADIRAC[server]==${CTADIRAC_VERSION} diracx-cli \
    rucio-clients==${RUCIO_VERSION} \
    ctao-bdms-rucio-policy==${RUCIO_POLICY_VERSION}

RUN mkdir -p /opt/dirac/etc/grid-security/certificates \
  && mkdir -p /home/dirac/.ssh

COPY --chown=dirac:dirac ./configure.py ./delete_section.py /home/dirac/
COPY --chown=dirac:dirac ./bashrc /opt/dirac/

ENV \
  DIRAC="${DIRACOS}" \
  CONDA_PREFIX="${DIRACOS}" \
  CONDOR_CONFIG="${DIRACOS}/etc/condor/condor_config" \
  DAVIX_DISABLE_REDIRECT_CACHING=1 \
  DAVIX_USE_LIBCURL=1 \
  GSETTINGS_SCHEMA_DIR="${DIRACOS}/share/glib-2.0/schemas" \
  MAMBA_ROOT_PREFIX="${DIRACOS}" \
  PATH="${DIRACOS}/bin:${PATH}" \
  X509_CERT_DIR="/etc/grid-security/certificates" \
  X509_VOMSES="${DIRACOS}/etc/grid-security/vomses" \
  X509_VOMS_DIR="${DIRACOS}/etc/grid-security/vomsdir" \
  XML_CATALOG_FILES="file://${DIRACOS}/etc/xml/catalog file:///etc/xml/catalog"
