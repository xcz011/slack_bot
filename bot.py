# -*- coding: utf-8 -*-
"""
Python Slack Bot class for use with the pythOnBoarding app
"""
import os
import message

from slackclient import SlackClient

# To remember which teams have authorized your app and what tokens are
# associated with each team, we can store this information in memory on
# as a global object. When your bot is out of development, it's best to
# save this in a more persistant memory store.
authed_teams = {}


class Bot(object):
    """ Instanciates a Bot object to handle Slack onboarding interactions."""
    def __init__(self):
        super(Bot, self).__init__()
        self.name = "pythonboardingbot"
        self.emoji = ":robot_face:"
        # When we instantiate a new bot object, we can access the app
        # credentials we set earlier in our local development environment.
        self.oauth = {"client_id": os.environ.get("CLIENT_ID"),
                      "client_secret": os.environ.get("CLIENT_SECRET"),
                      # Scopes provide and limit permissions to what our app
                      # can access. It's important to use the most restricted
                      # scope that your app will need.
                      "scope": "bot"}
        self.verification = os.environ.get("VERIFICATION_TOKEN")

        # NOTE: Python-slack requires a client connection to generate
        # an oauth token. We can connect to the client without authenticating
        # by passing an empty string as a token and then reinstantiating the
        # client with a valid OAuth token once we have one.
        self.client = SlackClient('xoxb-349472886132-uFeseSrE3ya7FeSz97SlFUeo')
        # We'll use this dictionary to store the state of each message object.
        # In a production envrionment you'll likely want to store this more
        # persistantly in  a database.
        self.messages = {}

    def auth(self, code):
        """
        Authenticate with OAuth and assign correct scopes.
        Save a dictionary of authed team information in memory on the bot
        object.

        Parameters
        ----------
        code : str
            temporary authorization code sent by Slack to be exchanged for an
            OAuth token

        """
        # After the user has authorized this app for use in their Slack team,
        # Slack returns a temporary authorization code that we'll exchange for
        # an OAuth token using the oauth.access endpoint
        auth_response = self.client.api_call(
                                "oauth.access",
                                client_id=self.oauth["client_id"],
                                client_secret=self.oauth["client_secret"],
                                code=code
                                )
        # To keep track of authorized teams and their associated OAuth tokens,
        # we will save the team ID and bot tokens to the global
        # authed_teams object
        team_id = auth_response["team_id"]
        authed_teams[team_id] = {"bot_token":
                                 auth_response["bot"]["bot_access_token"]}
        # Then we'll reconnect to the Slack Client with the correct team's
        # bot token
        self.client = SlackClient(authed_teams[team_id]["bot_token"])

    def open_dm(self, user_id):
        """
        Open a DM to send a welcome message when a 'team_join' event is
        recieved from Slack.

        Parameters
        ----------
        user_id : str
            id of the Slack user associated with the 'team_join' event

        Returns
        ----------
        dm_id : str
            id of the DM channel opened by this method
        """
        new_dm = self.client.api_call("im.open",
                                      user=user_id)
        dm_id = new_dm["channel"]["id"]
        return dm_id


    def post_message_by_channel(self, channel_id, msg, attach):
        post_message = self.client.api_call(
                            "chat.postMessage",
                            channel=channel_id,
                            text=msg,
                            attachments = attach
                            )
        print(post_message)
        return post_message

    def create_channel(self, channel_name):
        return_msg = self.client.api_call(
                            "groups.open",
                            name=channel_name,
                            )   
        # print(return_msg)
        return return_msg

    def update_msg(self, channel_id, ts, text, attachment):
        return_msg = self.client.api_call("chat.update",
                                channel=channel_id,
                                ts= ts,
                                text="Task Complete!",
                                attachments=attachment
                                )
        # print(return_msg)
        return return_msg
    def close_incident(self, channel_id, resolve_code, resolve_note, incident_id):
        post_message = self.client.api_call(
                            "chat.postMessage",
                            channel=channel_id,
                            attachments = [
                                            {
                                                "title": incident_id.upper() +" HAS BEEN CLOSED",
                                                "color": "#2eb886",
                                                "fields": [
                                                    {
                                                        "title": "Resolve code",
                                                        "value": resolve_code,
                                                        "short": "false"
                                                    },
                                                    {
                                                        "title": "Resolve Note",
                                                        "value": resolve_note,
                                                        "short": "false"
                                                    }
                                                ]                                                
                                            }
                                        ]
                        )
        return post_message              
                            
    def open_dialog(self, trigger_id, incident_id):
        return_msg = self.client.api_call("dialog.open",
                                trigger_id=trigger_id,
                                dialog={
                                        "callback_id": "Resolve_form",
                                        "title": "Resolve "+incident_id,
                                        "submit_label": "Submit",
                                        "elements": [{
                                                "type": "select",
                                                "label": "Resolution Code",
                                                "name": "Resolution Code",
                                                "options": [{
                                                        "value": "Solved (Work Around)",
                                                        "label": "Solved (Work Around)"
                                                    },
                                                    {
                                                        "value": "Solved (Permanently)",
                                                        "label": "Solved (Permanently)"
                                                    },
                                                    {
                                                        "value": "Not Solved (Not Reproducible)",
                                                        "label": "Not Solved (Not Reproducible)"
                                                    },
                                                    {
                                                        "value": "Not Solved (Too Costly)",
                                                        "label": "Not Solved (Too Costly)"
                                                    },
                                                    {
                                                        "value": "Closed/Resolved By Caller",
                                                        "label": "Closed/Resolved By Caller"
                                                    }
                                                ]
                                            },
                                            {
                                                "max_length": 500,
                                                "name": "Resolution Notes",
                                                "value": "",
                                                "placeholder": "",
                                                "min_length": 0,
                                                "label": "Resolution Notes",
                                                "type": "textarea"
                                            }
                                        ]
                                    }
                                
                                )
        print(return_msg)


