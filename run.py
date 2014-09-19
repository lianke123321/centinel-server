from app import app, db, models
import config
import os

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % (config.sqlite_db)
if not os.path.exists(config.sqlite_db):
    sql_dir = os.path.dirname(config.sqlite_db)
    if not os.path.exists(sql_dir):
        os.makedirs(sql_dir)
    db.create_all()
    # create an admin and client role
    db.session.add(models.Role('admin'))
    db.session.add(models.Role('client'))
    db.session.commit()
app.run(debug=True)
