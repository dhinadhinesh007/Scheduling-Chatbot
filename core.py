import slackclient, time
import random
import pymysql
import json
# delay in seconds before checking for new events 
SOCKET_DELAY = 1

# slackbot environment variables
SLACK_TOKEN='';
SLACK_NAME='testbot'
SLACK_ID = ''
slack_client = slackclient.SlackClient(SLACK_TOKEN)
connection =pymysql.connect(host='localhost',user='root', password='',db='smartplug',cursorclass=pymysql.cursors.DictCursor);

def is_private(event):
    """Checks if private slack channel"""
    return event.get('channel').startswith('D')
	
def get_mention(user):
    return '<@{user}>'.format(user=user)

slack_mention=get_mention(SLACK_ID);
	
def is_for_me(event):
    """Know if the message is dedicated to me"""
    # check if not my own event
    type = event.get('type')
    if type and type == 'message' and not(event.get('user')== SLACK_ID):
        # in case it is a private message return true
        if is_private(event):
            return True
        # in case it is not a private message check mention
        text = event.get('text')
        channel = event.get('channel')
        if slack_mention in text.strip().split():
            return True
        else:
            return False
			
def is_hi(message):
    tokens = [word.lower() for word in message.strip().split()]
    return any(g in tokens
               for g in ['hello', 'bonjour', 'hey', 'hi', 'sup', 'morning', 'hola', 'ohai', 'yo'])


def is_bye(message):
    tokens = [word.lower() for word in message.strip().split()]
    return any(g in tokens
               for g in ['bye', 'goodbye', 'revoir', 'adios', 'later', 'cya'])

			   
def is_schedule(message):
    tokens = [word.lower() for word in message.strip().split()]
    return any(g in tokens
            for g in ['schedule','plug','from', 'to'])
			   
			   
def say_hi(user_mention):
    """Say Hi to a user by formatting their mention"""
    response_template = random.choice(['Sup, {mention}...',
                                       'Yo!',
                                       'Hola {mention}',
                                       'Bonjour!'])
    return response_template.format(mention=user_mention)


def say_bye(user_mention):
    """Say Goodbye to a user"""
    response_template = random.choice(['see you later, alligator...',
                                       'adios amigo',
                                       'Bye {mention}!',
                                       'Au revoir!'])
    return response_template.format(mention=user_mention)
	
def update_db(message,val,channel):
    tokens = [word.lower() for word in message.strip().split()]
    print(tokens)
    usrid= val['User_ID'];
    cursor=connection.cursor();
    sql= "select Plug_Name from plug where User_ID='"+str(usrid)+"'";
    res=cursor.execute(sql);
    actions_list=list();
    if(not res):
        print('Query Not Successful');
    rows=cursor.fetchall();
    for row in rows:
        diction= dict();
        diction["name"]="plugs";
        diction["text"]=row['Plug_Name'];
        diction["type"]="button";
        diction["value"]=row['Plug_Name'];
        actions_list.append(diction);
    cursor.close();
    connection.commit();
    #print(actions_list);
    all_diction=dict();
    all_diction["name"]="plugs";
    all_diction["text"]="All of it.";
    all_diction["type"]="button";
    all_diction["value"]="All";
    actions_list.append(all_diction);
    Button_response={
	"text":"Seems like you have few plugs to manage.",
	"attachments":[
        {
            "text": "Which one do you want to schedule?",
            "fallback": "You are unable to choose a plug.",
            "callback_id": "plug_select",
            "color": "#3AA3E3",
            "attachment_type": "default",
        }
    ]
	}
    
    Button_response["attachments"][0]["actions"]=actions_list;
    #Button_response= json.dumps([Button_response]);
    #print(Button_response);
    #req_url="https://dhinesh_bots.testbot/slack/message_action";
    post_message(message=Button_response, channel=channel,attach=1)
    plug_name= receive_response();
	
    return;
    '''
    connection =pymysql.connect(host='localhost',user='root', password='',db='smartplug',cursorclass=pymysql.cursors.DictCursor);
    cursor= connection.cursor();
    sql="Update schedule set From_time= , To_time= where Plug_name='"+user_email+"'";
    res=cursor.execute(sql);
    if(not res):
        print('Query Not Successful');
    '''
	
def handle_message(message, user, channel):
    if is_hi(message):
        user_mention = get_mention(user)
        post_message(message=say_hi(user_mention), channel=channel,attach=0)
    elif is_bye(message):
        user_mention = get_mention(user)
        post_message(message=say_bye(user_mention), channel=channel,attach=0)
    elif is_schedule(message):
        user_mention= get_mention(user)
        post_message(message='Working on it...', channel=channel,attach=0)
        profile= slack_client.api_call('users.info', token=SLACK_TOKEN,
                          user=user)
		
        user_email= profile['user']['profile']['email'];
        connection =pymysql.connect(host='localhost',user='root', password='',db='smartplug',cursorclass=pymysql.cursors.DictCursor);
        cursor= connection.cursor();
        sql="select User_ID,Priority from users where Email='"+user_email+"'";
        res=cursor.execute(sql);
        if(not res):
            print('Query Not Successful');
        val=cursor.fetchone();
		#print("Query Successful");
        update_db(message,val,channel);
        cursor.close();
        connection.commit();
        connection.close();
		
	
	
def post_message(message, channel,attach):
    if(attach==0):
        slack_client.api_call('chat.postMessage', channel=channel,
                          text=message, as_user=True)
    else:
	    slack_client.api_call('chat.postMessage',text=message['text'],attachments=message['attachments'],channel=channel, as_user=True)
						  
def run():
    if slack_client.rtm_connect():
        print('[.] Testbot is ON...')
        while True:
            event_list = slack_client.rtm_read()
            if len(event_list) > 0:
                for event in event_list:
                   # print(event)
                    if is_for_me(event):
                        handle_message(message=event.get('text'), user=event.get('user'), channel=event.get('channel'))
            time.sleep(SOCKET_DELAY)
    else:
        print('[!] Connection to Slack failed...')

if __name__=='__main__':
    run()
