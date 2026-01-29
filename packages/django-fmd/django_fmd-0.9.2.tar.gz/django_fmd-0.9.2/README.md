# Django Find My Device

[![django-fmd @ PyPi](https://img.shields.io/pypi/v/django-fmd?label=django-fmd%20%40%20PyPi)](https://pypi.org/project/django-fmd/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-fmd)](https://gitlab.com/jedie/django-find-my-device/-/blob/main/pyproject.toml)
[![License GPL V3+](https://img.shields.io/pypi/l/django-fmd)](https://gitlab.com/jedie/django-find-my-device/-/blob/main/LICENSE)

Find My Device client and server implemented in Python using Django.
Usable for the Andorid App [**FindMyDevice**](https://gitlab.com/Nulide/findmydevice/) by [Nnulide](https://nulide.de/):

[<img src="https://fdroid.gitlab.io/artwork/badge/get-it-on.png" alt="Get FindMyDevice on F-Droid" height="80">](https://f-droid.org/packages/de.nulide.findmydevice/)

Note: For command notifications, you also need to install a https://unifiedpush.org/ app like "ntfy":

[<img src="https://fdroid.gitlab.io/artwork/badge/get-it-on.png" alt="Get ntfy on F-Droid" height="80">](https://f-droid.org/packages/io.heckel.ntfy)


# Django "Find My Device" server for YunoHost

[![Integration level](https://dash.yunohost.org/integration/django-fmd.svg)](https://dash.yunohost.org/appci/app/django-fmd) ![Working status](https://ci-apps.yunohost.org/ci/badges/django-fmd.status.svg) ![Maintenance status](https://ci-apps.yunohost.org/ci/badges/django-fmd.maintain.svg)
[![Install django-fmd with YunoHost](https://install-app.yunohost.org/install-with-yunohost.svg)](https://install-app.yunohost.org/?app=django-fmd)

## State

### Server implementation

What worked:

* App can register the device
* App can send a new location
* App can delete all server data by unregister the device
* The Web page can fetch the location of a device
* Paginate between locations in Web page
* Push notification of commands

Server TODOs:

* Pictures


### Client implementation

e.g.:
```bash
~/django-find-my-device$ ./manage.py fmd --get-location --device-id 2gvp8d --password your-password
```


## Start hacking:

```bash
~$ git clone https://gitlab.com/jedie/django-find-my-device.git
~$ cd django-find-my-device
~/django-find-my-device$ ./manage.py
...
(findmydevice) run_dev_server
```

There is also a docker dev. setup, e.g.:
```bash
~/django-find-my-device$ make up
```

Notes:

* The app will not accept self-signed certificates! So you need to use non-https URLs for testing.
* Django dev server and docker compose will bind to `0.0.0.0:8000` by default! So it's accessible from other devices in your network!


## credits

The *FindMyDevice* concept and the App/Web pages credits goes to [Nnulide](https://nulide.de/) the creator of the app FindMyDevice.

Currently, we store a copy of html/js/css etc. files from [findmydeviceserver/web/](https://gitlab.com/fmd-foss/fmd-server/-/tree/master/web) ([GNU GPLv3](https://gitlab.com/fmd-foss/fmd-server/-/blob/master/LICENSE))
into our project repository here:

 * [findmydevice/static/fmd_externals](https://gitlab.com/jedie/django-find-my-device/-/tree/main/findmydevice/static/fmd_externals)
 * [findmydevice/web/](https://gitlab.com/jedie/django-find-my-device/-/tree/main/findmydevice/web)
 *
This is done by [update_fmdserver_files.sh](https://gitlab.com/jedie/django-find-my-device/-/blob/main/update_fmdserver_files.sh) script.


## versions

[comment]: <> (✂✂✂ auto generated history start ✂✂✂)

* [v0.9.2](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.9.1...v0.9.2)
  * 2026-01-24 - Update requirements
  * 2025-11-08 - Fix adb_grant_fmd_rights.sh - permission must be set one by one!
  * 2025-11-01 - Enhance ADB script and try to set all permissions at once
* [v0.9.1](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.9.0...v0.9.1)
  * 2025-10-30 - Enhance admin around picture
  * 2025-10-30 - Remove the index for picture data to fix #9
  * 2025-10-30 - Remove brackets from admin link
  * 2025-10-30 - Add a link on the FMD web page into the Django Admin
  * 2025-10-30 - Redirect to login page directly
  * 2025-10-30 - Update requirements
* [v0.9.0](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.4.1...v0.9.0)
  * 2025-10-27 - Fix publishing
  * 2025-10-27 - NEW: Support to store and fetch pictures
  * 2025-10-27 - fix commands by storing all data and return it
  * 2025-10-27 - Add GetAllLocationsView
  * 2025-10-27 - fix push notification
  * 2025-10-27 - Fix broken html
  * 2025-10-27 - Update static html files (patched) from origin project
  * 2025-10-27 - Add test for PUT command
  * 2025-10-27 - Update PUT command: Seems that "Data" can't be None
  * 2025-10-27 - Fix dev. usage: We need the cache!
  * 2025-10-27 - fix web page access and tests
  * 2025-10-27 - gitlab.com/Nulide/findmydeviceserver/ -> gitlab.com/fmd-foss/fmd-server/
  * 2025-10-27 - expand logging if password is OK
  * 2025-10-27 - add "(Django Find My Device)" suffix to version, so it's displayed in the app
  * 2025-10-26 - Update client: Use correct /api/v1/ prefix
  * 2025-10-26 - comment deny_any_real_request() because of LiveServerTestCase
  * 2025-10-26 - Update PyCharm configs
  * 2025-10-26 - Bump version to v0.9.0 because is't the min. version
  * 2025-10-26 - fix docker setup
  * 2025-10-26 - Bugfix docker image build via "make build"
  * 2025-10-26 - cleanup: remove obsolete files
  * 2025-10-26 - Fix api/v1 prefix and serve ds.html page
  * 2025-10-26 - Update snapshot files
  * 2025-10-26 - Add PyCharm run config files
  * 2025-10-26 - Update project setup
  * 2024-07-03 - Use getpass() in CLI
* [v0.4.1](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.4.0...v0.4.1)
  * 2024-06-18 - fix CI
  * 2024-06-18 - Manually append slash redirect only for /admin/
  * 2024-06-18 - Fix WebPageRedirectView: Use full url
  * 2024-06-18 - Update history

<details><summary>Expand older history entries ...</summary>

* [v0.4.0](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.3.2...v0.4.0)
  * 2024-06-17 - Reimplement the client and manage command
  * 2024-06-17 - GET "/version" via FmdClient
  * 2024-06-17 - Update FmdClient.request_access()
  * 2024-06-17 - Test get_salt() via FmdClient()
  * 2024-06-17 - Patch by </head>
  * 2024-06-17 - Use 'fmd_externals/favicon.ico' in admin, too.
  * 2024-06-17 - Add docker compose setup for development
  * 2024-06-17 - Handle Data="unused"
  * 2024-06-17 - Fix favicon.ico request
  * 2024-06-16 - Bugfix wrong password compare in /requestAccess (Don't lowercase!)
  * 2024-06-16 - Handle request location index "NaN"
  * 2024-06-16 - update PUT /key
  * 2024-06-16 - Update Device model
  * 2024-06-16 - Expand hashed_password model field
  * 2024-06-16 - Fix web lage static file urls
  * 2024-06-16 - +"argon2-cffi"
  * 2024-06-16 - Update API changes
  * 2024-06-16 - Update static web page files
  * 2024-06-16 - Refactor: "run_testserver" -> "run_dev_server"
  * 2024-06-13 - Update project setup
  * 2022-08-10 - Add script to grant FMD permission via adb
  * 2022-08-10 - Update README.md
* [v0.3.2](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.3.1...v0.3.2)
  * 2022-08-10 - Test project Autologin only for `/admin/` requests
  * 2022-08-10 - Expand database field length
* [v0.3.1](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.3.0...v0.3.1)
  * 2022-08-10 - Bugfix static files for YunoHost
* [v0.3.0](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.2.0...v0.3.0)
  * 2022-08-10 - fix code style
  * 2022-08-10 - Add FMD client demo script
  * 2022-08-10 - remove `logic.js`patches
  * 2022-08-08 - Bugfix classifiers
  * 2022-08-08 - update requirements
  * 2022-08-08 - Bugfix Client: Server accepts "Data" only as String.
  * 2022-08-08 - Log server error messages
  * 2022-08-08 - Log if key requested with "Data" != "0"
  * 2022-08-08 - Remove debug
  * 2022-08-04 - Implement a Python Client for FMD
  * 2022-08-03 - Move FMD web page static files to "real django static" files
  * 2022-07-31 - Add missing leaflet image files
  * 2022-07-31 - Replace device UUID with a short string
  * 2022-07-19 - Include external JS/CSS files
* [v0.2.0](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.1.3...v0.2.0)
  * 2022-07-19 - Remove unused "POST /push"
  * 2022-07-19 - Check push service calls
  * 2022-07-19 - Update README.md
  * 2022-07-19 - Implement command push notifications
  * 2022-07-19 - code refactoring
  * 2022-07-19 - Store User-Agent in Device and Location
  * 2022-07-19 - updates
* [v0.1.3](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.1.2...v0.1.3)
  * 2022-07-12 - remove obsolete publish.py file
  * 2022-07-12 - Run tests before publishing
  * 2022-07-12 - release 0.1.3
  * 2022-07-12 - Lower 'No "IDT"' error log.
  * 2022-07-12 - update tests
  * 2022-07-12 - Patch 'applicatoin/json' -> 'application/json'
  * 2022-07-12 - Remove "@Nulide FMDServer" from index.html
* [v0.1.2](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.1.1...v0.1.2)
  * 2022-07-12 - release v0.1.2
  * 2022-07-12 - Enhance Device change list: Location count + last update info
  * 2022-07-12 - Add login page for anonymous users
  * 2022-07-12 - Better Device.__str__() (for admin changelist filter etc.)
* [v0.1.1](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.1.0...v0.1.1)
  * 2022-07-12 - Bugfixes
* [v0.1.0](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.0.4...v0.1.0)
  * 2022-07-12 - Release v0.1.0
  * 2022-07-12 - Add optional name for Devices (Only for django admin)
  * 2022-07-12 - Update tests
  * 2022-07-12 - Pimp Location admin
  * 2022-07-12 - Pimp Devices admin
  * 2022-07-12 - Rename "Device User" to "Device"
  * 2022-07-12 - Serve fmd page "index.html" with own view and only for authenticated users
  * 2022-07-12 - Use settings.PATH_URL if exists for `site_url`
  * 2022-07-12 - Use own Admin Site class and expand admn tests
  * 2022-07-12 - Redirect to the FMD web page
  * 2022-07-12 - Add link to project page into page footer via version
* [v0.0.4](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.0.3...v0.0.4)
  * 2022-07-12 - Update logic.js - Make all requests "relative"
  * 2022-07-12 - Bugfix location put requests and not defined `put_data`
* [v0.0.3](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.0.2...v0.0.3)
  * 2022-07-12 - Bugfix store location because of too large `raw_date` field value
  * 2022-07-11 - Update README.md
* [v0.0.2](https://gitlab.com/jedie/django-find-my-device/-/compare/v0.0.1...v0.0.2)
  * 2022-07-11 - Release v0.0.2
  * 2022-07-11 - Expand CI test matrix
  * 2022-07-11 - Support Python 3.7
  * 2022-07-05 - setup coverage report in CI
  * 2022-07-05 - fix darker
  * 2022-07-05 - fix tests
  * 2022-07-05 - setup gitlab CI
  * 2022-07-05 - Expand README
  * 2022-07-05 - add update_fmdserver_files.sh
* [v0.0.1](https://gitlab.com/jedie/django-find-my-device/-/compare/11d09ec...v0.0.1)
  * 2022-07-05 - init v0.0.1
  * 2022-07-05 - Configure SAST in `.gitlab-ci.yml`, creating this file if it does not already exist

</details>


[comment]: <> (✂✂✂ auto generated history end ✂✂✂)
