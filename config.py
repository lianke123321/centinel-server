import os
import getpass

# misc
recommended_version = 1.1

# user details
current_user    = getpass.getuser()
centinel_home   = os.path.join(os.path.expanduser('~'+current_user),
                               '.centinel')

# directory structure
results_dir     = os.path.join(centinel_home, 'results')
experiments_dir = os.path.join(centinel_home, 'experiments')
inputs_dir = os.path.join(centinel_home, 'inputs')

# sql
DATABASE_URI = "postgresql://postgres:postgres@localhost/centinel"

maxmind_db      = os.path.join(centinel_home, 'maxmind.mmdb')

# AS information lookup
net_to_asn_file      = os.path.join(centinel_home, 'data-raw-table')
asn_to_owner_file    = os.path.join(centinel_home, 'data-used-autnums')

# web server
ssl_cert = "server.iclab.org.crt"
ssl_key  = "server.iclab.org.key"
ssl_chain = "server.iclab.org_bundle.crt"
