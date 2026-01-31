FROM harbor.cta-observatory.org/proxy_cache/almalinux:9

ARG DIRACOS_VERSION="2.54"
ARG CTADIRAC_VERSION="3.0.11"
ARG RUCIO_VERSION="38.2.0"
ARG RUCIO_POLICY_VERSION="0.2.1"
ARG USERID=1000
ARG GROUPID=1000

ENV DIRAC_DIR="/ctadirac/${CTADIRAC_VERSION}"

RUN \
  dnf install -y \
    epel-release \
    https://cvmrepo.s3.cern.ch/cvmrepo/yum/cvmfs-release-latest.noarch.rpm \
  && dnf install -y \
    apptainer \
    cvmfs \
    inotify-tools \
    openssh-clients \
    openssh-server \
    procps \
    python-unversioned-command \
    python3 \
    nodejs \
  && cvmfs_config setup

RUN cd /etc/ssh && ssh-keygen -A

COPY default.local /etc/cvmfs/default.local
COPY ctao.dpps.test.conf /etc/cvmfs/config.d/ctao.dpps.test.conf
COPY --chmod=600 --chown=root:root 100-sshd_only_public_key_auth.conf /etc/ssh/sshd_config.d/100-sshd_only_public_key_auth.conf

RUN mkdir -p /etc/grid-security/certificates /etc/grid-security/vomsdir/ctao.dpps.test /etc/grid-security/vomses \
 && touch /etc/grid-security/vomses/ctao.dpps.test

RUN \
  if getent group ${GROUPID}; then \
    groupmod --new-name dirac $(getent group ${GROUPID} | cut -d: -f1); \
  else \
    groupadd --gid ${GROUPID} dirac;\
  fi \
  && adduser --uid ${USERID} --gid dirac -s /bin/bash -d /home/dirac dirac \
  && mkdir -p /home/dirac/.ssh /home/dirac/data ${DIRAC_DIR} && chown -R dirac:dirac /home/dirac /ctadirac

# install as dirac user
USER dirac
# Install DIRAC client
RUN cd /tmp \
    && curl -LO https://github.com/DIRACGrid/DIRACOS2/releases/download/${DIRACOS_VERSION}/DIRACOS-Linux-x86_64.sh \
    && bash DIRACOS-Linux-x86_64.sh -p ${DIRAC_DIR}/Linux-x86_64 \
    && rm -f DIRACOS-Linux-x86_64.sh \
    && source ${DIRAC_DIR}/Linux-x86_64/diracosrc \
    && pip install --no-cache-dir \
      CTADIRAC[pilot]==${CTADIRAC_VERSION} rucio-clients==${RUCIO_VERSION} \
      ctao-bdms-rucio-policy==${RUCIO_POLICY_VERSION} \
    && ln -s ${DIRAC_DIR} /ctadirac/pro

USER root
COPY entrypoint.sh /entrypoint.sh
CMD ["/entrypoint.sh"]
