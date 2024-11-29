from flask import Blueprint, current_app, url_for, request, session, redirect, flash
from flask_login import current_user, login_user
from app.models import User, SocialAccount
from app import db, oauth
from datetime import datetime, timedelta
from app.utils import get_redirect_target

bp = Blueprint('social', __name__)

# OAuth providers configuration
oauth.init_app(current_app)

# Google OAuth
google = oauth.remote_app(
    'google',
    consumer_key=current_app.config.get('GOOGLE_CLIENT_ID'),
    consumer_secret=current_app.config.get('GOOGLE_CLIENT_SECRET'),
    request_token_params={
        'scope': 'email profile'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth'
)

# Facebook OAuth
facebook = oauth.remote_app(
    'facebook',
    consumer_key=current_app.config.get('FACEBOOK_CLIENT_ID'),
    consumer_secret=current_app.config.get('FACEBOOK_CLIENT_SECRET'),
    request_token_params={'scope': 'email'},
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    access_token_method='GET',
    authorize_url='https://www.facebook.com/dialog/oauth'
)

# Twitter OAuth
twitter = oauth.remote_app(
    'twitter',
    consumer_key=current_app.config.get('TWITTER_CLIENT_ID'),
    consumer_secret=current_app.config.get('TWITTER_CLIENT_SECRET'),
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate'
)

@bp.route('/login/google')
def google_login():
    return google.authorize(callback=url_for('social.google_authorized', _external=True))

@bp.route('/login/facebook')
def facebook_login():
    return facebook.authorize(callback=url_for('social.facebook_authorized', _external=True))

@bp.route('/login/twitter')
def twitter_login():
    return twitter.authorize(callback=url_for('social.twitter_authorized', _external=True))

@bp.route('/login/google/authorized')
def google_authorized():
    resp = google.authorized_response()
    if resp is None or resp.get('access_token') is None:
        flash('Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        ))
        return redirect(url_for('auth.login'))
    
    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    return handle_oauth_response('google', me.data['id'], me.data.get('email'),
                               me.data.get('name'), resp['access_token'])

@bp.route('/login/facebook/authorized')
def facebook_authorized():
    resp = facebook.authorized_response()
    if resp is None or resp.get('access_token') is None:
        flash('Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        ))
        return redirect(url_for('auth.login'))
    
    session['facebook_token'] = (resp['access_token'], '')
    me = facebook.get('/me?fields=id,email,name')
    return handle_oauth_response('facebook', me.data['id'], me.data.get('email'),
                               me.data.get('name'), resp['access_token'])

@bp.route('/login/twitter/authorized')
def twitter_authorized():
    resp = twitter.authorized_response()
    if resp is None:
        flash('Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        ))
        return redirect(url_for('auth.login'))
    
    session['twitter_token'] = (resp['oauth_token'], resp['oauth_token_secret'])
    return handle_oauth_response('twitter', resp['user_id'],
                               None, resp['screen_name'], resp['oauth_token'])

def handle_oauth_response(provider, social_id, email, username, access_token):
    if not social_id:
        flash('Authentication failed.')
        return redirect(url_for('auth.login'))
    
    social_account = SocialAccount.query.filter_by(
        provider=provider,
        social_id=social_id
    ).first()
    
    if social_account:
        user = social_account.user
        social_account.access_token = access_token
        social_account.updated_at = datetime.utcnow()
        db.session.commit()
    else:
        if current_user.is_authenticated:
            user = current_user
        elif email:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(username=username, email=email)
                db.session.add(user)
        else:
            user = User(username=username)
            db.session.add(user)
        
        social_account = SocialAccount(
            user=user,
            provider=provider,
            social_id=social_id,
            username=username,
            email=email,
            access_token=access_token
        )
        db.session.add(social_account)
        db.session.commit()
    
    login_user(user, True)
    return redirect(get_redirect_target())
