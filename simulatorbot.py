from slackclient import SlackClient
import random
from ast import literal_eval
import os
import time
import sys
import traceback

BOT_TOKEN = os.environ['SIMULATORBOT_TOKEN']
SEARCH_TOKEN = os.environ['SIMULATORBOT_SEARCH_TOKEN']
BOT_ID = os.environ['SIMULATORBOT_ID']
AT_BOT = "<@" + BOT_ID + ">"
VOCAB_FILE = os.environ['VOCAB_FILE']


class SimulatorBot(object):
  def __init__(self, vocab_file):
    self.cli = SlackClient(BOT_TOKEN)
    assert self.cli.rtm_connect()
    self.bot_name = self.cli.api_call("users.info", user=BOT_ID)['user']['name']
    self.vocab_file = vocab_file
    self.counter = 0
    self.dict = {}
  
  def update_dict(self):
    print 'Updating...'
    self.post('Diagnostic message: Currently updating vocab file, bot will be down for about 30 seconds', "#random")
    self.dict = {None: []}
    
    cli2 = SlackClient(SEARCH_TOKEN)
    assert cli2.rtm_connect()
    
    # todo: pagination-insensitive API call assumes there are no more than 100
    # channels; works for this workspace but may not work for other workspaces
    channels = cli2.api_call(
      "conversations.list",
      types="public_channel,private_channel,im")['channels']
    channel_ids = [c['id'] for c in channels]
    
    for cid in channel_ids:
      cursor = None
      while True:
        kwargs = {'channel': cid, 'count': 1000}
        if cursor:
          kwargs['cursor'] = cursor
        history = cli2.api_call("conversations.history", **kwargs)
        messages = history['messages']
        for m in messages:
          words = m['text'].split()
          if words:  # e.g. uploaded image is a message w/o text
            self.dict[None].append(words[0])
          for i in range(len(words)):
            source_word = words[i]
            dest_word = words[i+1] if i+1 in range(len(words)) else None
            if source_word in self.dict:
              self.dict[source_word].append(dest_word)
            else:
              self.dict[source_word] = [dest_word]
        if history['has_more']:
          cursor = history['response_metadata']['next_cursor']
        else:
          break
        time.sleep(1.2)  # slack rate limit (max 50 history calls per minute)
    
    with open(self.vocab_file, 'w') as f:
      f.write(str(self.dict))
    
    # patch: the websocket closes after being idle too long; sometimes the
    # dictionary update takes long enough
    self.cli = SlackClient(BOT_TOKEN)
    assert self.cli.rtm_connect()
    
    print 'Update done.'
    self.post('Diagnostic message: Finished updating vocab file and bot is back up', "#random")
  
  def gen(self):
    with open(self.vocab_file, 'r') as f:
      self.dict = literal_eval(f.read())
    
    output = []
    word = None
    while True:
      word = random.choice(self.dict[word])
      if word is None:
        break
      output.append(word)
    return u' '.join(output)
  
  def post(self, msg, channel, to_user=None):
    self.cli.api_call("chat.postMessage",
                 channel=channel,
                 text=msg,
                 as_user=True)
  
  def is_command(self, output):
    try:
      assert output['type'] == 'message'
      text = output.get('text', '').upper()
      assert AT_BOT in text or self.bot_name.upper() in text
      assert output['user'] != BOT_ID
      return True
    except AssertionError:
      return False
  
  def run(self):
    print 'Running'
    while True:
      try:
        # heroku ephemeral file support: if vocabulary doesn't exist, create it
        if not os.path.isfile(self.vocab_file):
          self.update_dict()
        for output in self.cli.rtm_read():
          if self.is_command(output):
            self.post(self.gen(), output['channel'], output['user'])
            self.counter = 0
        time.sleep(1)
        self.counter += 1
        # if the bot hasn't posted in 6 hours
        if self.counter % (3600*6) == 0:
          self.post(self.gen(), "#random")
      except Exception:
        traceback.print_exc()
        self.post(traceback.format_exc(), "#random")


if __name__ == '__main__':
  SimulatorBot(VOCAB_FILE).run()

