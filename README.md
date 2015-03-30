### Centinel server

The Server used to control Centinel nodes in the wild.

### Install and usage
#### Preparation (all platforms)
Get the maxind geolocation database by running 

    $ mkdir ~/.centinel
    $ curl http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.mmdb.gz -o ~/.centinel/maxmind.db

Download and install PostgreSQL [here](http://www.postgresql.org/download/).
Create user root:

    $ sudo -u postgres createuser -s root

Create a new Database: 

    $ createdb -U root --locale=en_US.utf-8 -E utf-8 -O root centinel -T template0

Install psycopg2:

    $ pip install -U psycopg2


It is recommended that you run Python version > 2.7.9 and Werkzeug version >= 0.10.0 for better TLS support.

#### Debian & OS X
    $ pip install flask flask-httpauth flask-sqlalchemy passlib geoip2 netaddr postgres
    $ python run.py

### Supported platforms
    * Unix
    * Mac OS X
