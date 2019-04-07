from slackclient import SlackClient
import os
import time

SLACK_HISTORY_TOKEN = os.environ['SLACK_HISTORY_TOKEN']


def backup(dirname):
  """
  Backs up slack history to a directory of text files, where the name of each
  text file is the channel name (or channel ID if a DM channel).
  """
  if not os.path.isdir(dirname):
    print(f'Directory {dirname} does not exist.')
    return
  
  print('Starting...')
  
  cli = SlackClient(SLACK_HISTORY_TOKEN)
  assert cli.rtm_connect()
  
  # todo: pagination-insensitive API call assumes there are no more than 100
  # channels; works for this workspace but may not work for other workspaces
  channels = cli.api_call(
    "conversations.list",
    types="public_channel,private_channel,mpim,im")['channels']
  
  count = 0
  
  for c in channels:
    messages = []
    cursor = None
    while True:
      kwargs = {'channel': c['id'], 'count': 1000}
      if cursor:
        kwargs['cursor'] = cursor
      history = cli.api_call("conversations.history", **kwargs)
      messages.extend(history['messages'])  
      if history['has_more']:
        cursor = history['response_metadata']['next_cursor']
      else:
        break
      time.sleep(1.2)  # slack rate limit (max 50 history calls per minute)
    
    filename = c.get('name') or c['id']
    with open(f'{dirname}/{filename}', 'w') as f:
      f.write(str(messages))
    count += len(messages)
  
  print(f'Finished backing up {count} messages.')


if __name__ == '__main__':
  backup(input('Name of output directory: '))

