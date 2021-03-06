import os
import pytest

from flask import _request_ctx_stack
import flask_login

# the app won't initialize without an environment variable pointing
# to the config file
os.environ['EMOL_CONFIG'] = '/home/vagrant/source/config/test/config.py'

SETUP_JSON = """{"encryption_key":"0123456789012345", "admin_emails":["ealdormere.emol@gmail.com"], "waiver_reminders":
[30, 60], "disciplines":[{"name":"Rapier","slug":"rapier","authorizations":{"heavy-rapier":"Heavy Rapier",
"cut-thrust":"Cut & Thrust","two-weapon":"Two Weapon","parry-device":"Parry Device"},"marshals":{"marshal":"Marshal"},
"reminders_at": [30, 60]}, {"name":"Armoured Combat","slug":"armoured-combat","authorizations":{"weapon-shield":
"Weapon & Shield", "great-weapon":"Great Weapon","two-weapon":"Two Weapon","siege":"Siege"},"marshals":{"marshal":
"Marshal"}, "reminders_at": [30, 60]}]}"""

from emol.app import create_app
the_app = create_app()
from emol.api.admin_api import SetupApi
SetupApi.test_setup(SETUP_JSON)

from emol.models import Combatant, User
from emol.utility.testing import Mockmail


@pytest.fixture(scope='session')
def app():
    """Flask-thing requires an 'app' fixture on everything."""
    yield the_app


# User fixtures


@pytest.fixture(scope='module')
def admin_user(app):
    """Log in the admin user"""
    user = User.query.filter(User.email == 'ealdormere.emol@gmail.com').one()
    flask_login.login_user(user)

    yield user


@pytest.fixture
def unprivileged_user(app):
    """An unprivileged user."""
    user = User(email='u_user@ealdormere.ca', system_admin=False)
    app.db.session.add(user)
    app.db.session.commit()
    flask_login.login_user(user)

    yield user

    app.db.session.delete(user)
    app.db.session.commit()


@pytest.fixture(params=['roles'])
def privileged_user(app, admin_user, unprivileged_user, request):
    """Log in a user and assign the given roles.

    Roles are given as a dict of lists:
    {
        None: [list of global roles],
        'discipline_slug': [list of roles for discipline_slug],
        ...
    }

    """
    # Log in admin user to assign roles
    flask_login.logout_user()
    flask_login.login_user(admin_user)

    for key, roles in request.param.items():
        unprivileged_user.add_roles(key, roles)

    # Log in now-privileged user for the test
    flask_login.logout_user()
    flask_login.login_user(unprivileged_user)
    app.db.session.commit()

    yield unprivileged_user

    flask_login.logout_user()

    # Make sure unprivileged user really is
    unprivileged_user.roles.clear()
    assert len(unprivileged_user.roles) == 0


@pytest.fixture
def combatant_data():
    return dict(
        legal_name='Fred McFred',
        sca_name='Fred Fredsson',
        original_email='mcfred@mailinator.com',
        email='mcfred@mailinator.com',
        phone=2125551212,
        address1='123 Main Street',
        address2='Apartment 12',
        city='Anytown',
        province='ON',
        postal_code='A1A 1A1',
        waiver_date='2015-01-01'
    )


@pytest.fixture
def fixture_user(app):
    """A user that isn't privileged_user for combatant to do its thing."""
    user = User(email='fixture@ealdormere.ca', system_admin=False)
    user.add_roles(None, ['edit_combatant_info', 'edit_waiver_date'])
    user.add_roles('rapier', ['edit_authorizations'])
    user.add_roles('armoured-combat', ['edit_authorizations'])
    app.db.session.add(user)

    flask_login.logout_user()
    flask_login.login_user(user)

    yield user

    app.db.session.delete(user)


@pytest.fixture
def combatant(app, combatant_data, fixture_user):

    # Fixture wants no email sent, with no check for sent/not-sent
    with Mockmail('emol.models.privacy_acceptance', None):
        c = Combatant.create(combatant_data)
        c.get_card('rapier', create=True)

    flask_login.logout_user()

    yield c

    app.db.session.delete(c)
    app.db.session.commit()


@pytest.fixture
def login_client(app):
    """Test client with the user pulled by the calling test logged in."""
    user = getattr(_request_ctx_stack.top, 'user', None)
    assert user is not None

    with app.test_client() as c:
        c.post('/api/test-login/{0.id}'.format(user))

        yield c