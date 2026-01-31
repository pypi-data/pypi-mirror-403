#! /bin/bash

source /home/dirac/diracos/diracosrc
export X509_CERT_DIR="${DIRACOS}/etc/grid-security/certificates"
export X509_VOMSES="${DIRACOS}/etc/grid-security/vomses"
export X509_VOMS_DIR="${DIRACOS}/etc/grid-security/vomsdir"
exec "$@"
