import os
import getpass

recommended_versions = ["1.1"]
current_user = getpass.getuser()
centinel_home = os.path.join(os.path.expanduser('~'+current_user), '.centinel')
results_dir = os.path.join(centinel_home, 'results')
experiments_dir = os.path.join(centinel_home, 'experiments')
clients_file = os.path.join(centinel_home, 'clients')
