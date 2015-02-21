### Centinel server

The Server used to control Centinel nodes in the wild.

### Install and usage
#### All
    Get the maxind geolocation database by running 
	$ mkdir ~/.centinel
    $ curl http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.mmdb.gz -o ~/.centinel/maxmind.db

	First Download and install postgresql [here](http://www.postgresql.org/download/)
	Create New User root with password root : sudo -u postgres createuser -s root
	Create a new Database: 
	         createdb -U root --locale=en_US.utf-8 -E utf-8 -O root centinel -T template0
	install psycopg2 : pip install -U psycopg2
#### Debian
    $ apt-get install python-flask python-passlib python-flask-httpauth python-flask-sqlalchemy
    $ pip install geoip2
    $ python run.py

#### OSX
    $ pip install flask flask-httpauth flask-sqlalchemy passlib geoip2
    $ python run.py

### Supported platforms
    * Unix
