#!/bin/bash

# Script to grant extra permissions to FMD app via adb.
#
# Install "adb", e.g.:
#   ~$ sudo apt install adb
#
#   * Connect Andorid device to PC.
#   * run this script
#   * grant permissions for this USB connection
#
#
# Most important permission that needs to be granted via adb is:
#   android.permission.WRITE_SECURE_SETTINGS
#
# See: https://fmd-foss.org/docs/fmd-android/granting-secure-settings-access/
#
# But we just set all app permissions listed in the manifest, see:
# https://gitlab.com/fmd-foss/fmd-android/-/blob/master/app/src/main/AndroidManifest.xml
#

# App package name:
FMD_NAME="de.nulide.findmydevice"

# If dev version is used, uncomment the following line:
#FMD_NAME="package:de.nulide.findmydevice.dev"

DATE_STRING=$(date +"%Y-%m-%dT%H%M%S")
DUMPSYS_BEFORE_FILE="fmd_dumpsys_${DATE_STRING}_before.txt"
DUMPSYS_AFTER_FILE="fmd_dumpsys_${DATE_STRING}_after.txt"
DUMPSYS_DIFF_FILE="fmd_dumpsys_${DATE_STRING}_diff.txt"

PERMISSIONS=(
  android.permission.SEND_SMS
  android.permission.READ_SMS
  android.permission.RECEIVE_SMS
  android.permission.ACCESS_COARSE_LOCATION
  android.permission.ACCESS_FINE_LOCATION
  android.permission.ACCESS_BACKGROUND_LOCATION
  android.permission.POST_NOTIFICATIONS
  android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
  android.permission.RECEIVE_BOOT_COMPLETED
  android.permission.ACCESS_NOTIFICATION_POLICY
  android.permission.ACCESS_NETWORK_STATE
  android.permission.ACCESS_WIFI_STATE
  android.permission.CHANGE_WIFI_STATE
  android.permission.INTERNET
  android.permission.SYSTEM_ALERT_WINDOW
  android.permission.READ_PHONE_STATE
  android.permission.CAMERA
  android.permission.RECORD_AUDIO
  android.permission.BIND_NOTIFICATION_LISTENER_SERVICE
  android.permission.WRITE_SECURE_SETTINGS
  android.permission.BLUETOOTH
  android.permission.BLUETOOTH_ADMIN
  android.permission.BLUETOOTH_CONNECT
)

verbose_call() {
    echo "____________________________________________________________________________"
    set -x
    "$@"
    set +x
}

# List all USB devices:
verbose_call lsusb

# Just list connected device:
verbose_call adb devices

# Get the user ids
verbose_call adb shell pm list users

verbose_call adb shell pm list packages | grep findmydevice
if [ $? -ne 0 ]; then
  echo "findmydevice package not found. Aborting."
  exit 1
fi

# Store current permissions:
verbose_call adb shell dumpsys package ${FMD_NAME} > ${DUMPSYS_BEFORE_FILE}

# Grant permissions:
for PERM in "${PERMISSIONS[@]}"; do
    verbose_call adb shell pm grant ${FMD_NAME} $PERM
done

# Store updated permissions:
verbose_call adb shell dumpsys package ${FMD_NAME} > ${DUMPSYS_AFTER_FILE}

# Display diff of before and after dumpsys:
verbose_call diff ${DUMPSYS_BEFORE_FILE} ${DUMPSYS_AFTER_FILE} > ${DUMPSYS_DIFF_FILE} || true
verbose_call cat ${DUMPSYS_DIFF_FILE}


