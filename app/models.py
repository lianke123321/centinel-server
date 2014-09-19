from app import db
from app import app

from datetime import datetime
from passlib.apps import custom_app_context as pwd_context

roles_tab = db.Table('roles_tab',
                     db.Column('user_id', db.Integer,
                               db.ForeignKey('clients.id')),
                     db.Column('role_id', db.Integer,
                               db.ForeignKey('role.id')))


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(36), index=True)  # uuid length=36
    password_hash = db.Column(db.String(64))
    # there are at most 15 chars for ip plus 4 for netmask plus 1 for
    # space, so 20 total chars
    last_ip = db.Column(db.String(20))
    last_seen = db.Column(db.DateTime)
    registered_date = db.Column(db.DateTime)
    has_given_consent = db.Column(db.Boolean)
    date_given_consent = db.Column(db.DateTime)
    is_vpn = db.Column(db.Boolean)
    # we expect this to be a country code (2 chars)
    country = db.Column(db.String(2))

    # since a user can have multiple roles, we have a table to hold
    # the mapping between users and their roles
    roles = db.relationship('Role', secondary=roles_tab,
                            backref=db.backref('users', lazy='dynamic'))

    def __init__(self, username, password, roles=['client'],
                 kwargs={}):
        """Create a client object.

        Note: we set kwargs to an empty dict by default so that
        everything below will always work (kwargs.get(key) returns
        None if the key is not in the dict)

        """
        self.username = username
        self.password_hash = pwd_context.encrypt(password)
        roles_to_add = []
        for role in roles:
            role = Role.query.filter_by(name=role).first()
            roles_to_add.append(role)
        self.roles = roles_to_add

        # process the json/keyword args to set the remaining
        # variables.
        # Note: we are not doing this programmatically to prevent
        # security problems
        if kwargs.get('ip') is not None:
            ip = kwargs.get('ip')
            self.last_ip = ".".join(ip.split(".")[:3]) + ".0/24"
        if kwargs.get('vpn'):
            self.is_vpn = kwargs.get('vpn')
        if kwargs.get('consent'):
            self.has_given_consent = kwargs.get('consent')
            self.date_given_consent = datetime.now()
        country = kwargs.get('country')
        if country is not None and (len(country) == 2):
            self.country = country
        # we are not automatically doing this because we may want to
        # create users without them ever connecting
        if kwargs.get('last_seen'):
            self.last_seen = kwargs.get('last_seen')

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))

    def __init__(self, name):
        self.name = name

