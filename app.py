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

TASK_IDS = {}
task_id = 'LB-2375'

# Attachment JSON containing our link button
# For this demo app, The task ID should be the last segment of the URL
attach_json = [
    {
        "fallback": "Upgrade your Slack client to use messages like these.",
        "color": "#CC0000",
        "actions": [
            {
                "type": "button",
                "text": ":red_circle:   Complete Task: " + task_id,
                "url": "https://e2cb80d8.ngrok.io/workflow/" + task_id,
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
        bot_id = slack_event['event']['bot_id']
        if bot_id == 'BA4CME96X':
            # channel_id= slack_event['event']['channel']
            # print(channel_id)
            
            # get incident id
            incident_id = slack_event['event']['attachments'][0]['title']
            print(incident_id)

            # get incident detail 
            attachments = slack_event['event']['attachments']
            attach_json = json.dumps(attachments)

            # create channel
            channel_id = pyBot.create_channel(incident_id)
            print(channel_id)
            # pyBot.post_message_by_channel(channel_id, '',attach_json)
        # res = pyBot.post_message_by_channel(channel_id, 'Let\'s get started!',attach_json)
        # TASK_IDS[task_id] = {
        #             'channel': res['channel'],
        #             'ts': res['message']['ts']
        #         }
        
        
        
        make_response('success', 200, {"content_type":"application/json" } )

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

# @app.route("/workflow/<task_id>", methods=['GET'])
# def test(task_id):

#     task_form = """<form method="POST" action="/complete/{}">
#                     <input type="submit" value="Do The Thing" />
#                 </form>""".format(task_id)

#     return make_response(task_form, 200)

# @app.route("/complete/<task_id>", methods=['POST'])
# def complete(task_id):
#     """
#     This is where your app's business logic would live.
#     Once the task has been complete, the user will be directed to this `/complete`
#     page, which shows a link back to their Slack conversation
#     """

#     # When this page loads, we update the original Slack message to show that
#     # the pending task has been completed
#     attach_json = [
#         {
#             "fallback": "Upgrade your Slack client to use messages like these.",
#             "color": "#36a64f",
#             "text": ":white_check_mark:   *Completed Task: {}*".format(task_id),
#             "mrkdwn_in": ["text"]
#         }
#     ]
#     res = slack.api_call(
#         "chat.update",
#         channel=TASK_IDS[task_id]["channel"],
#         ts=TASK_IDS[task_id]["ts"],
#         text="Task Complete!",
#         attachments=attach_json
#     )

#     # Get the message permalink to redirect the user back to Slack
#     res = slack.api_call(
#         "chat.getPermalink",
#         channel=TASK_IDS[task_id]["channel"],
#         message_ts=TASK_IDS[task_id]["ts"]
#     )

#     # Link the user back to the original message
#     slack_link = "<a href=\"{}\">Return to Slack</a>".format(res['permalink'])

#     # Redirect the user back to their Slack conversation
#     return make_response("Task Complete!<br/>" + slack_link, 200)

if __name__ == '__main__':
    app.run(debug=True)
