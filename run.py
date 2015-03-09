import argparse
import centinel
import centinel.models
import centinel.views
import config
from OpenSSL import SSL
import os

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adhoc', help='Use adhoc SSL key and certificate.',
                        action='store_true')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    db = centinel.db
    app = centinel.app   
    db.create_all()

    Role = centinel.models.Role

    admin_role = db.session.query(Role).filter(Role.name=='admin').all()
    if len(admin_role) == 0:
        db.session.add(Role('admin'))

    client_role = db.session.query(Role).filter(Role.name=='client').all()
    if len(client_role) == 0:
        db.session.add(Role('client'))

    db.session.commit()
    if args.adhoc:
        context='adhoc'
    else:
        # default method should be TLS
        context = SSL.Context(SSL.TLSv1_METHOD)
        context.use_privatekey_file(config.ssl_key)
        context.use_certificate_file(config.ssl_cert)
        context.load_verify_locations(config.ssl_chain)

    # Also, I shouldn't have to say this, but *DO NOT COMMIT THE
    # KEY*. Under no circumstances should the key be committed
    app.run(host="0.0.0.0", port=8082, debug=True,
            ssl_context=context)
