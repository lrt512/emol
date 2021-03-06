# -*- coding: utf-8 -*-
"""The home page and its associated views."""

from authomatic import Authomatic
from authomatic.adapters import WerkzeugAdapter
from flask import Blueprint, render_template, request, make_response
from flask import abort, url_for, redirect, session, current_app
from flask_login import current_user, login_user, logout_user, login_required

from emol.exception.combatant import CombatantDoesNotExist
from emol.exception.privacy_acceptance import PrivacyPolicyNotAccepted
from emol.mail import Emailer
from emol.models import User, Combatant, UpdateRequest

BLUEPRINT = Blueprint('home', __name__)

@BLUEPRINT.route('/')
def index():
    """The home page.

    Display the user home page if someone is logged in,
    else display the nouser home page

    """
    if current_user.is_anonymous is True:
        return render_template('home/nouser.html')
    elif current_user.is_admin is True:
        return redirect(url_for('user_admin.user_list'))
    else:
        return redirect(url_for('combatant_admin.combatant_stats'))


@BLUEPRINT.route('/login', methods=['GET', 'POST'])
def login():
    """Use Authomatic to log a user in.

    Once Authomatic has done its thing, check against
    valid users to allow or invalidate the login session.

    Note that this URL needs to be registered as an authorized
    redirect URI in the credentials for the webapp:

    Be logged in as the Google account that will own eMoL
    Go to: https://console.developers.google.com
    Select Credentials
    Create credentials for the app

    Authorize the Google+ API

    The client ID and client secret go into config.py
        as consumer_key and consumer_secret in the OAUTH2 section
    Set this URL (http://example.com/login) as an authorized redirect URI

    """
    session.clear()
    response = make_response()

    authomatic = Authomatic(
        current_app.config['AUTHOMATIC_CONFIG'],
        current_app.config['AUTHOMATIC_SECRET']
    )

    result = authomatic.login(
        WerkzeugAdapter(request, response), 'google'
    )

    if result:
        if result.user:
            result.user.update()
            # User is logged in, now check against our user table
            print(result.user)
            user = User.query.filter(
                User.email == result.user.email
            ).one_or_none()

            if user is None:
                # No.
                abort(401)
            else:
                # Yes!
                login_user(user)
                return redirect(url_for('home.index'))

    if request.method == 'POST':
        abort(500)
    else:
        return response


@BLUEPRINT.route('/logout', methods=['GET'])
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    return redirect(url_for('home.index'))


@BLUEPRINT.route('/request-card', methods=['GET', 'POST'])
def request_card():
    """Handle GET and POST methods for card requests."""
    if request.method == 'GET':
        return render_template('home/request_card.html')
    elif request.method == 'POST':
        email = request.form['request-card-email']
        msg = None
        try:
            combatant = Combatant.get_by_email(email)
            mailer = Emailer()
            mailer.send_card_request(combatant)
            msg = (
                'An email has been sent with instructions '
                'for retrieving your card'
            )
        except CombatantDoesNotExist:
            msg = 'No combatant found with email "{0}'.format(email)
        except PrivacyPolicyNotAccepted as exc:
            current_app.logger.error(
                'Card request for {0} (privacy not accepted)'
                    .format(combatant.email)
            )
            msg = str(exc)

        return render_template('message/message.html', message=msg)

    else:
        abort(405)


@BLUEPRINT.route('/update-info', methods=['GET', 'POST'])
def update_info():
    """Handle GET and POST methods for info update requests."""
    if request.method == 'GET':
        return render_template('home/update_info.html')
    elif request.method == 'POST':
        email = request.form['update-info-email']
        try:
            combatant = Combatant.get_by_email(email)
            update_request = UpdateRequest(combatant=combatant)
            current_app.db.session.add(update_request)
            current_app.db.session.commit()

            # Mail it
            mailer = Emailer()
            mailer.send_info_update(combatant, update_request)
            msg = (
                'An email has been sent with instructions for '
                'updating your information'
            )
        except CombatantDoesNotExist:
            msg = 'No combatant found with email {0}'.format(email)
        except PrivacyPolicyNotAccepted as exc:
            current_app.logger.error(
                'Card request for {0} (privacy not accepted)'
                    .format(combatant.email)
            )
            msg = str(exc)

        return render_template('message/message.html', message=msg)
    else:
        abort(405)


@BLUEPRINT.route('/embed-message', methods=['GET'])
def message():
    """Render the message view."""
    return render_template('message/message_embed.html')
