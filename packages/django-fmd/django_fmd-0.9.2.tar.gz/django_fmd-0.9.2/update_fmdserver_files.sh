#!/bin/bash

# Download the "master" version of the current "web" files:
# https://gitlab.com/fmd-foss/fmd-server/-/tree/master/web
#
# Store them in the "static/fmd_externals" directory and the "index.html" in the "web" directory.

DST="$(pwd)/findmydevice"

set -x

(
    cd /tmp
    wget --timestamp https://gitlab.com/fmd-foss/fmd-server/-/archive/master/fmd-server-master.zip
    unzip -u fmd-server-master.zip "fmd-server-master/web/*" -d /tmp/fmdserver/

    rm -Rf "${DST}/static/"
    mkdir -p "${DST}/static/fmd_externals/"
    mv /tmp/fmdserver/fmd-server-master/web/* "${DST}/static/fmd_externals/"

    rm -Rf "${DST}/web/"
    mkdir "${DST}/web/"
    mv "${DST}/static/fmd_externals/index.html" "${DST}/web/index.html"
    mv "${DST}/static/fmd_externals/ds.html" "${DST}/web/ds.html"
)

.venv/bin/python update_fmdserver_files.py
