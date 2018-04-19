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

FLAG = 1 

# Attachment JSON containing our link button
# For this demo app, The task ID should be the last segment of the URL
button_json = [
        {
            "text": "Can you solve this incient?",
            "fallback": "You are good",
            "callback_id": "wopr_game",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "actions": [
                {
                    "name": "approve",
                    "text": "✔️ Yes",
                    "style": "primary",
                    "type": "button",
                    "value": "accept",
                },
                {
                    "name": "dontapprove",
                    "text": "🚫 No",
                    "style": "danger",
                    "type": "button",
                    "value": "no-accept"
                }
            ]
        }
]

finish_json = [
 {
            "text": "Plugging in skype cable for Marketing?",
            "fallback": "You are unable to help here",
            "callback_id": "wopr_game",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "actions": [
                {
                    "name": "game",
                    "text": ":heavy_check_mark: You have accepted a task",
                    "style": "danger",
                    "type": "button",
                    "value": "no-accept"
                }
            ]
        }
]

not_accept_json = [
 {
            "text": "Plugging in skype cable for Marketing?",
            "fallback": "You are unable to help here",
            "callback_id": "wopr_game",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "actions": [
                {
                    "name": "game",
                    "text": ":heavy_check_mark: Please reroute the task",
                    "style": "danger",
                    "type": "button",
                    "value": "no-accept"
                }
            ]
        }
]

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



@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # handle the button action
    print('******************')
    form_json = json.loads(request.form["payload"])
    print(form_json)
    print('*******************')
    ts = form_json['original_message']['ts']
    text = form_json['original_message']['text']
    channel_id =  form_json['channel']['id']
    action =  form_json['actions'][0]['name']
    if action == 'approve':
        pyBot.update_msg(channel_id, ts, text, finish_json)
    else:
        pyBot.update_msg(channel_id, ts, text, not_accept_json)
    return make_response('', 200)


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
    print('**********new event happenning... ********************************************')
    # print(slack_event)
    print('******************************************************************************')
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
        try:
            bot_id = slack_event['event']['bot_id']
            channel_id= slack_event['event']['channel']
        except:
            bot_id = 'BAANR2N871'
            channel_id ='error'
        
        if bot_id == 'BAANR2N87':
            pyBot.post_message_by_channel('CAAR4N9D5', '', button_json)
            # get incident id
            try:
                incident_id = slack_event['event']['attachments'][0]['title']
                print(incident_id)
            except:
                incident_id = 'error'

            # get incident detail 
            attachments = slack_event['event']['attachments']
            attach_json = json.dumps(attachments)

            # create channel by incident id 
            pyBot.post_message_by_channel(channel_id, 'channel ' + incident_id + ' is going to be created','')
            new_channel_id = create_channel(incident_id)
            print('new_channel_id is '+ new_channel_id)
            print('inivte user and bot')
            jen = 'UA9466PFB'
            invite_channel(new_channel_id, jen)
            invite_channel(new_channel_id, 'BAANR2N87')

            # post message
            pyBot.post_message_by_channel(new_channel_id, '', attach_json)
            
            # accept button
            pyBot.post_message_by_channel(new_channel_id, '', button_json)
        
        
        make_response('success', 200, {"content_type":"application/json" } )

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

def create_channel(channel_name):
    url = "https://slack.com/api/channels.create"
    querystring = {
            "token":"xoxp-348978265808-349142776593-349062225280-53bb042be67927ebfbd372bd2f39101e",
            "name":channel_name
    }

    headers = {
    'Cache-Control': "no-cache"
    }
    
    response = requests.request("POST", url, headers=headers, params=querystring)
    res = response.json()
    print( res)
    try:
        new_channel_id = res['channel']['id']
    except:
        new_channel_id = 'CAAR4N9D5'
    return new_channel_id


def invite_channel(channel_id, user_id):
    url = "https://slack.com/api/channels.invite"
    querystring = {
            "token":"xoxp-348978265808-349142776593-349062225280-53bb042be67927ebfbd372bd2f39101e",
            "channel": channel_id,
            "user": user_id
    }

    headers = {
    'Cache-Control': "no-cache"
    }
    
    response = requests.request("POST", url, headers=headers, params=querystring)
    res = response.json()
    print( res)



if __name__ == '__main__':
    app.run(debug=True)
