import os
import getpass

# misc
recommended_version = 1.1

# user details
current_user        = getpass.getuser()
centinel_home       = os.path.join(os.path.expanduser('~'+current_user), '.centinel')

# directory structure
results_dir         = os.path.join(centinel_home, 'results')
clients_file        = os.path.join(centinel_home, 'clients')
experiments_dir     = os.path.join(centinel_home, 'experiments')
