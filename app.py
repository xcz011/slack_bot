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
            "text": "Are you the right person to resolve this incident?",
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

suggestion_solution_json = [
        {
            "text": "Would you like see previous solution related to this incident?",
            "fallback": "You are good",
            "callback_id": "wopr_game",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "actions": [
                {
                    "name": "need_solution",
                    "text": "✔️ Sure, show me",
                    "style": "primary",
                    "type": "button",
                    "value": "accept",
                },
                {
                    "name": "noneed_solution",
                    "text": "🚫 No, I've got it!",
                    "style": "danger",
                    "type": "button",
                    "value": "no-accept"
                }
            ]
        }
]

showsolution_json = [
        {
            "text": "Would you like see previous solution related to this incident?",
            "fallback": "You are good",
            "callback_id": "wopr_game",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "fields": [
                {
                    "title": "✔️ Suggestion is coming...."
                                   }
            ]
        }
]
finish_json = [
 {
            "text": "Can you solve this incient?",
            "fallback": "You are unable to help here",
            "callback_id": "wopr_game",
            "color": "#00ff00",
            "attachment_type": "default",
            "fields": [
                {
                    "title": "✔️ You have accepted a task"
                                   }
            ]
        }
]

not_accept_json = [
 {
            "text": "Can you solve this incient?",
            "fallback": "You are unable to help here",
            "callback_id": "wopr_game",
            "color": "#800000",
            "attachment_type": "default",
            "fields": [
                {
                    "title": "🚫 Please route this incident to correct group"
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

@app.route("/slack/resolve", methods=["POST"])
def resolve():
    # Parse the request payload
    print('enter button process area')
    print(request.form)
    trigger_id = request.form.get('trigger_id', None)
    channel_name = request.form.get('channel_name', None)
    print(channel_name)
    # get sys_id
    sys_id = get_sysid_by_incident(channel_name)
    print(sys_id)

    #open dialog
    pyBot.open_dialog(trigger_id, channel_name)
    
    return make_response('', 200)

@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # handle the button action

    print('enter button process area')
    form_json = json.loads(request.form["payload"])
    print(form_json)
    if form_json['type'] == 'dialog_submission':
        # update the serviceNow to resolvation status
        res_code = form_json['submission']['Resolution Code']
        res_note = form_json['submission']['Resolution Notes']
        incident_id = form_json['channel']['name']
        channel_id = form_json['channel']['id']
        sys_id = get_sysid_by_incident(incident_id)
        print(res_code, res_note, incident_id, sys_id)
        
        # resolve the incident in serviceNow
        resolve_incident(sys_id, res_note, res_code)
        
        #post msg back to user
        pyBot.close_incident(channel_id, res_code, res_note, incident_id)
        pyBot.post_message_by_channel(channel_id,'*Going to archive this channel...*','')

        # archive the channel
        archive_channel(channel_id)


    else:
        ts = form_json['original_message']['ts']
        text = form_json['original_message']['text']
        channel_id =  form_json['channel']['id']
        incident_name = form_json['channel']['name']
        sys_id = get_sysid_by_incident(incident_name)
        action =  form_json['actions'][0]['name']
        print('**************')
        print(form_json['actions'][0])
        print('**************')
        # print(sys_id, incident_name)
        if action == 'approve':
            pyBot.update_msg(channel_id, ts, text, finish_json)

            print("update the serviceNow...")
            update_incident(sys_id)
            pyBot.post_message_by_channel(channel_id, '✔️ Update incident to In progress', '')

            # post point to user channel
            jen = 'UA9466PFB'
            dm_id = pyBot.open_dm(jen)

            pyBot.post_message_by_channel(dm_id, '', [
                                            {   "color": "#2eb886",
                                                "fields": [
                                                    {
                                                        "title": 'Thanks for your help, you just got 2 spotlight point for accepting ' + incident_name.upper()
                                                    },
                                                    {
                                                        "title": "Have a nice Day",
                                                        "value": ":smiley:"
                                                    }
                                                ]                                                
                                            }
                                        ])
            
            # post second question
            pyBot.post_message_by_channel(channel_id, '', suggestion_solution_json)
        elif action == 'need_solution':
            pyBot.update_msg(channel_id, ts, text, showsolution_json)

            # call api and post solution
            att = solution_suggest('What are the assumptions of ordinary least squares regression?')
            print(type(att))
            print(att['text'])
            print(att['attachments'])
            pyBot.post_message_by_channel(channel_id, att['text'],  att['attachments'])
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

    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                             })

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
            # get incident id
            try:
                incident_id = str(slack_event['event']['attachments'][0]['text']).split('|')[1].split('>')[0]
                print(incident_id)
            except:
                incident_id = 'error'

            # get incident detail 
            attachments = slack_event['event']['attachments']
            # print('*******************************')
            # print(attachments)
            # print('*******************************')
            attach_json = json.dumps(attachments)

            # create channel by incident id 
            pyBot.post_message_by_channel(channel_id, 'channel ' + incident_id + ' is going to be created','')
            new_channel_id = create_channel(incident_id)
            print('new_channel_id is '+ new_channel_id)

            # get fixer name
            fileds = slack_event['event']['attachments'][0]['fields']
            user_name = ''
            for di in fileds:
                if di['title'] == 'Assigned to':
                   user_name = di['value']
                elif di['title'] == 'Priority':
                   priority = di['value']

            print('inivte user and bot and chat with user')
            jen = 'UA9466PFB'
            dm_id = pyBot.open_dm(jen)

            pyBot.post_message_by_channel(dm_id, '', [
                                            {

                                                "color": "#2eb886",
                                                "fields": [
                                                    {
                                                        "title": 'You have been assigned '+ incident_id.upper(),
                                                        "short": "false"
                                                    },
                                                    {
                                                        "title": "Priority" + priority,
                                                        "short": "false"
                                                    }
                                                ]                                                
                                            }
                                        ])

            invite_channel(new_channel_id, jen)
            invite_channel(new_channel_id, 'BAANR2N87')

            # post message
            pyBot.post_message_by_channel(new_channel_id, '', attach_json)
            
            # accept button
            pyBot.post_message_by_channel(new_channel_id,  user_name + ' : Welcome to the channel !', button_json)

            
            

            # make_response('success', 200, {"content_type":"application/json" } )
        
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

def archive_channel(channel_id):
    url = "https://slack.com/api/channels.archive"
    querystring = {
            "token":"xoxp-348978265808-349142776593-349062225280-53bb042be67927ebfbd372bd2f39101e",
            "channel": channel_id
    }

    headers = {
        'Cache-Control': "no-cache"
    }
    
    response = requests.request("POST", url, headers=headers, params=querystring)
    res = response.json()

def update_incident(sys_id):
    url = 'https://pncmelliniumfalcon.service-now.com/api/now/table/incident/'+sys_id

    # Eg. User name="admin", Password="admin" for this code sample.
    user = 'han.solo'
    pwd = 'HanSolo2018'

    # Set proper headers
    headers = {"Content-Type":"application/json","Accept":"application/json"}

    # Do the HTTP request
    response = requests.put(url, auth=(user, pwd), headers=headers ,data="{\"incident_state\":\"In Progress\"}")

    # Check for HTTP codes other than 200
    if response.status_code != 200: 
        print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:',response.json())
        exit()

    # Decode the JSON response into a dictionary and use the data
    data = response.json()
    print(data)

def get_sysid_by_incident(incident_id):
    # Eg. User name="admin", Password="admin" for this code sample.
    user = 'han.solo'
    pwd = 'HanSolo2018'

    # Set proper headers
    headers = {"Content-Type":"application/json","Accept":"application/json"}
    
    # Do the HTTP request
    url = 'https://pncmelliniumfalcon.service-now.com/api/now/table/incident?sysparm_query=number%3D{}&sysparm_fields=sys_id%2Cnumber'.format(incident_id)

    
    response = requests.get(url, auth=(user, pwd), headers=headers )
    data = response.json()
    return data['result'][0]['sys_id']

def resolve_incident(sys_id, close_note, resolve_code):
    # Eg. User name="admin", Password="admin" for this code sample.
    user = 'han.solo'
    pwd = 'HanSolo2018'

    # Set proper headers
    headers = {"Content-Type":"application/json","Accept":"application/json"}
    
    # Do the HTTP request
    url = 'https://pncmelliniumfalcon.service-now.com/api/now/table/incident/' + sys_id

    data = {
        "close_code" : str(resolve_code),
        "close_notes": str(close_note),
        "state"      : "Resolved"
    }
    response = requests.put(url, auth=(user, pwd), headers=headers, data= str(data))


def solution_suggest(description):

    url = 'http://16ad2ae7.ngrok.io/get_solutions'
    payload = "{\"description\": \"What are the assumptions of ordinary least squares regression?\",\n    \"max_responses\": 3\n}"
    headers = {"Content-Type":"application/json","Accept":"application/json"}

    response = requests.post(url,  headers=headers ,data=payload)
    data = response.json()
    return data

if __name__ == '__main__':
    app.run(debug=True)
