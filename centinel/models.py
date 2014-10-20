from datetime import datetime
from passlib.apps import custom_app_context as pwd_context

import centinel
db = centinel.db
app = centinel.app

# constants
# 15 chars for ip + 4 for netmask
IP_ADDR_LEN = 19
COUNTRY_CODE_LEN = 2


roles_tab = db.Table('roles_tab',
                     db.Column('user_id', db.Integer,
                               db.ForeignKey('clients.id')),
                     db.Column('role_id', db.Integer,
                               db.ForeignKey('role.id')))


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(36), index=True)  # uuid length=36
    password_hash = db.Column(db.String(76))
    last_ip = db.Column(db.String(IP_ADDR_LEN))
    last_seen = db.Column(db.DateTime)
    registered_date = db.Column(db.DateTime)
    has_given_consent = db.Column(db.Boolean)
    date_given_consent = db.Column(db.DateTime)
    typeable_handle = db.Column(db.String(8))
    is_vpn = db.Column(db.Boolean)
    country = db.Column(db.String(COUNTRY_CODE_LEN))

    # since a user can have multiple roles, we have a table to hold
    # the mapping between users and their roles
    roles = db.relationship('Role', secondary=roles_tab,
                            backref=db.backref('users', lazy='dynamic'))

    def __init__(self, **kwargs):
        """Create a client object"""

        # only process the keys that we know about and that don't have
        # custom functionality. Also do type checking on the variable
        # type

        allowed_keys = {"username": "string", "is_vpn": bool,
                        "has_given_consent": bool,
                        "date_given_consent": datetime}
        for key in kwargs:
            if key not in allowed_keys:
                continue

            if (allowed_keys[key] is "string" or
                (isinstance(kwargs[key], allowed_keys[key]))):
                setattr(self, key, kwargs[key])

        if 'typeable_handle' in kwargs:
            self.typeable_handle = kwargs['typeable_handle']
        if 'password' in kwargs:
            self.password_hash = pwd_context.encrypt(kwargs['password'])
        if 'roles' in kwargs:
            get_role = lambda role: Role.query.filter_by(name=role).first()
            self.roles = [get_role(role) for role in kwargs['roles']]
        if 'ip' in kwargs:
            ip = kwargs['ip']
            # if there is a space between the ip and the netmask,
            # remove it
            ip = "".join(ip.split())
            # if there is no netmask,then truncate down to /24
            if "/" not in ip:
                ip = ".".join(ip.split(".")[:3]) + ".0/24"
            self.last_ip = ip
            self.is_vpn = kwargs.get('vpn')
        if 'consent' in kwargs:
            self.date_given_consent = datetime.now()
        country = kwargs.get('country')
        if country is not None and (len(country) == 2):
            self.country = country
        # if we have a date for the last time the client was seen,
        # then add it, otherwise, we won't add the last seen date in
        # case we need to remove it for security reasons or traveling
        if 'last_seen' in kwargs:
            self.last_seen = kwargs['last_seen']

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))

    def __init__(self, name):
        self.name = name
