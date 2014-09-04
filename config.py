import os
import getpass

class configuration(object):
	SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
	DEBUG = False
	TESTING = False

class developmentConfig(configuration):
	DEBUG = True

class testingConfig(configuration):
	TESTING = True

# misc
recommended_version = 1.1

# user details
current_user        = getpass.getuser()
centinel_home       = os.path.join(os.path.expanduser('~'+current_user), '.centinel')

# directory structure
results_dir         = os.path.join(centinel_home, 'results')
experiments_dir     = os.path.join(centinel_home, 'experiments')

