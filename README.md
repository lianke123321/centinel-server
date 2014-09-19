### Centinel server

The Server used to control Centinel nodes in the wild.

### Install and usage
#### All
    Get the maxind geolocation database by running 
	$ mkdir ~/.centinel
    $ curl http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.mmdb.gz -o ~/.centinel/maxmind.db

#### Debian
    $ apt-get install python-flask python-passlib python-flask-httpauth python-flask-sqlalchemy
    $ pip install geoip2
    $ python run.py

#### OSX
    $ pip install flask flask-httpauth flask-sqlalchemy passlib
    $ python run.py
	$ pip install flask flask-httpauth flask-sqlalchemy passlib geoip2

### Supported platforms
    * Unix
