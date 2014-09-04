import os
import getpass

# misc
recommended_version = 1.1

# user details
current_user        = getpass.getuser()
centinel_home       = os.path.join(os.path.expanduser('~'+current_user), '.centinel')

# directory structure
results_dir         = os.path.join(centinel_home, 'results')
experiments_dir     = os.path.join(centinel_home, 'experiments')

# sqlite
sqlite_db = 'sqlite:///db.sqlite'
