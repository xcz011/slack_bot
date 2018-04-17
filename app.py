# -*- coding: utf-8 -*-
"""
A routing layer for the onboarding bot tutorial built using
[Slack's Events API](https://api.slack.com/events-api) in Python
"""
import json
import bot
import requests
import os
from flask import Flask, request, make_response, render_template
from slackclient import SlackClient

pyBot = bot.Bot()
slack = pyBot.client

app = Flask(__name__)


@app.route("/thanks", methods=["GET", "POST"])
def thanks():
    """
    This route is called by Slack after the user installs our app. It will
    exchange the temporary authorization code Slack sends for an OAuth token
    which we'll save on the bot object to use later.
    To let the user know what's happened it will also render a thank you page.
    """
    # Let's grab that temporary authorization code Slack's sent us from
    # the request's parameters.
    code_arg = request.args.get('code')
    # The bot's auth method to handles exchanging the code for an OAuth token
    pyBot.auth(code_arg)
    return render_template("thanks.html")


@app.route("/listening", methods=["GET", "POST"])
def hears():
    """
    This route listens for incoming events from Slack and uses the event
    handler helper function to route events to our Bot.
    """
    # ============= Slack URL Verification ============ #
    # In order to verify the url of our endpoint, Slack will send a challenge
    # token in a request and check for this token in the response our endpoint
    # sends back.
    #       For more info: https://api.slack.com/events/url_verification
    slack_event = json.loads(request.data)
    print(slack_event)
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                             })

    # ============ Slack Token Verification =========== #
    # We can verify the request is coming from Slack by checking that the
    # verification token in the request matches our app's settings
    if pyBot.verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s \npyBot has: \
                   %s\n\n" % (slack_event["token"], pyBot.verification)
        # By adding "X-Slack-No-Retry" : 1 to our response headers, we turn off
        # Slack's automatic retries during development.
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    # ====== Process Incoming Events from Slack ======= #
    # If the incoming request is an Event we've subcribed to
    if "event" in slack_event:
        # webhook_url = 'https://hooks.slack.com/services/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'
        # slack_data = {'text': "this is xu testing, please ignore, thanks"}


        # webhook_url = 'https://slack.com/api/channels.create'
        # slack_data = {'token': "EBjxX0eKxAlUw2gUxNrFulRF",
        #               'name': 'xu_test_channel',
        #               'validate': 'true'
        #             }
        
        # response = requests.post(
        #     webhook_url, data=json.dumps(slack_data),
        #     headers={'Content-Type': 'application/json'}
        # )
        channel_id = slack_event['event']['item']['channel']
        print((type(slack_event)))
        pyBot.post_message_by_channel(channel_id, 'channel id is'+ channel_id)
        
        
        
        make_response('success', 200, {"content_type":"application/json" } )

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


if __name__ == '__main__':
    app.run(debug=True)
