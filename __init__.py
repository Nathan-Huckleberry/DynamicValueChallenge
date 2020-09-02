from CTFd.plugins.challenges import BaseChallenge, CTFdStandardChallenge, CHALLENGE_CLASSES
from CTFd.plugins import register_plugin_assets_directory
from CTFd.models import (
    ChallengeFiles,
    Challenges,
    Fails,
    Flags,
    Hints,
    Solves,
    Tags,
    db,
)
from CTFd import utils
from CTFd.plugins.migrations import upgrade
from CTFd.utils.modes import get_model
import math, os, urllib, requests
from flask import request, redirect
from CTFd.utils.decorators import admins_only

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")
STREAMLABS_API_BASE = 'https://www.streamlabs.com/api/v1.0'
ACCESS_TOKEN=None
REFRESH_TOKEN=None

class CTFdStreamChallenge(CTFdStandardChallenge):
    id = "stream"  # Unique identifier used to register challenges
    name = "stream"  # Name of a challenge type
    templates = {  # Templates used for each aspect of challenge editing & viewing
        "create": "/plugins/StreamLabsCTFdChallenge/assets/create.html",
        "update": "/plugins/challenges/assets/update.html",
        "view": "/plugins/challenges/assets/view.html",
    }

    def refresh_token():
        global ACCESS_TOKEN
        global REFRESH_TOKEN
        r = requests.post(STREAMLABS_API_BASE+"/token", data = {
            'grant_type': 'refresh_token',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'refresh_token': REFRESH_TOKEN})
        ACCESS_TOKEN=r.json()['access_token']
        REFRESH_TOKEN=r.json()['refresh_token']
        print(r.text)


    def send_first_blood(challenge, user):
        CTFdStreamChallenge.refresh_token()
        r = requests.post(STREAMLABS_API_BASE+"/alerts", data = {
            'access_token': ACCESS_TOKEN,
            'type': 'donation',
            'message': '{} got first blood on {}!'.format(user.name, challenge.name),
            'image_href': 'https://i.ibb.co/9n10Bp7/blood.gif'
        })
        print(r.text)

    def send_first_three(challenge, user):
        CTFdStreamChallenge.refresh_token()
        r = requests.post(STREAMLABS_API_BASE+"/alerts", data = {
            'access_token': ACCESS_TOKEN,
            'type': 'donation',
            'message': '{} got first three on {}!'.format(user.name, challenge.name),
            'image_href': 'https://i.ibb.co/rsPqS9D/flag2.gif'
        })
        print(r.text)

    @classmethod
    def callback(cls, challenge, user):
        Model = get_model()

        solve_count = (
            Solves.query.join(Model, Solves.account_id == Model.id)
            .filter(
                Solves.challenge_id == challenge.id,
                Model.hidden == False,
                Model.banned == False,
            )
            .count()
        )

        db.session.commit()

        if(solve_count == 1):
            print("first blood")
            CTFdStreamChallenge.send_first_blood(challenge, user)

        elif(solve_count <= 3):
            print("first three")
            CTFdStreamChallenge.send_first_three(challenge, user)

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)
        try:
            CTFdStreamChallenge.callback(challenge, user)
        except Exception as e:
            print(e)

def load(app):
    @app.route('/stream_labs_authorize', methods=['GET'])
    @admins_only
    def stream_labs_authorize():
        url = STREAMLABS_API_BASE+"/authorize?"
        params = {'client_id': CLIENT_ID,
                  'redirect_uri': REDIRECT_URI,
                  'response_type': 'code',
                  'scope': 'donations.read donations.create alerts.create'}
        full_url = url + urllib.parse.urlencode(params)
        return "<a href=" + full_url + ">Authorize with Streamlabs!</a>"

    @app.route('/stream_labs_oauth', methods=['GET'])
    @admins_only
    def stream_labs_oauth():
        code = request.args.get('code')
        print(code)
        r = requests.post(STREAMLABS_API_BASE+"/token", data = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'code': code})
        print(r.text)
        global ACCESS_TOKEN
        global REFRESH_TOKEN
        ACCESS_TOKEN=r.json()['access_token']
        REFRESH_TOKEN=r.json()['refresh_token']
        return redirect("/")

    upgrade()
    CHALLENGE_CLASSES['stream'] = CTFdStreamChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/StreamLabsCTFdChallenge/assets/"
    )
