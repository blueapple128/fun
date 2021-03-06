import slackclient
import websocket
import random
from ast import literal_eval
import os
import time
import traceback
import sys

# ad hoc way to set up multiple bot instances on different slack workspaces
# The 'right' solution is to spin up more than one heroku app each with its own
# set of config vars
# But that would incur a charge :P
assert len(sys.argv) == 2
PREFIX = sys.argv[1].upper()
BOT_TOKEN = os.environ[f'{PREFIX}_SIMULATORBOT_TOKEN']
SEARCH_TOKEN = os.environ[f'{PREFIX}_SIMULATORBOT_SEARCH_TOKEN']
WHITELISTED_NONPUBLIC_CHANNELS = (
  os.environ[f'{PREFIX}_WHITELISTED_NONPUBLIC_CHANNELS'].split(',')
)
DIAGNOSTIC_CHANNEL = "#_test"  # where to post update and crash recovery notices
BIGRAM_WEIGHT = 0.8


class SimulatorBot:
  def __init__(self):
    self.cli = slackclient.SlackClient(BOT_TOKEN)
    assert self.cli.rtm_connect()
    auth = self.cli.api_call("auth.test")
    self.bot_id = auth['user_id']
    self.bot_name = auth['user']
    self.vocab_file = f"{auth['team']}.vocab"
    self.dict = {}
    self.user_id_to_name = {}
    users = self.cli.api_call("users.list")['members']
    for u in users:
      self.user_id_to_name[u['id']] = u['profile']['display_name'] or u['profile']['real_name']
  
  def inform_update_start(self):
    print('Updating...')
    # todo: time will vary depending on number of channels in the workspace and
    # number of messages in the channel
    return self.post('Diagnostic message: Currently updating vocab file, bot will be down for about 30 seconds', DIAGNOSTIC_CHANNEL)
  
  def allowed_channel_ids(self, cli2):
    # todo: pagination-insensitive API call assumes there are no more than 100
    # channels; works for this workspace but may not work for other workspaces
    channels = cli2.api_call(
      "conversations.list",
      types="public_channel,private_channel,mpim,im")['channels']
    return [
      c['id']
      for c in channels
      if c['id'].startswith('C') or c['id'] in WHITELISTED_NONPUBLIC_CHANNELS
    ]
  
  def add_words_to_vocab(self, words):
    # unigrams
    self.dict[None].append(words[0])
    for i in range(len(words)):
      source_word = words[i]
      dest_word = words[i+1] if i+1 in range(len(words)) else None
      if source_word in self.dict:
        self.dict[source_word].append(dest_word)
      else:
        self.dict[source_word] = [dest_word]
    
    # bigrams
    if len(words) >= 2:
      if (None, words[0]) in self.dict:
        self.dict[(None, words[0])].append(words[1])
      else:
        self.dict[(None, words[0])] = [words[1]]
      for i in range(len(words) - 1):
        source_words = (words[i], words[i+1])
        dest_word = words[i+2] if i+2 in range(len(words)) else None
        if source_words in self.dict:
          self.dict[source_words].append(dest_word)
        else:
          self.dict[source_words] = [dest_word]
  
  def inform_update_end(self, response):
    # patch: the websocket closes after being idle too long; sometimes the
    # dictionary update takes long enough
    self.cli = slackclient.SlackClient(BOT_TOKEN)
    assert self.cli.rtm_connect()
    print('Update done.')
    self.cli.api_call("chat.delete",
      channel=response['channel'],
      ts=response['ts'])
  
  def update_dict(self):
    response = self.inform_update_start()
    self.dict = {None: []}
    
    cli2 = slackclient.SlackClient(SEARCH_TOKEN)
    assert cli2.rtm_connect()
    
    for cid in self.allowed_channel_ids(cli2):
      cursor = None
      while True:
        kwargs = {'channel': cid, 'count': 1000}
        if cursor:
          kwargs['cursor'] = cursor
        history = cli2.api_call("conversations.history", **kwargs)
        messages = history['messages']
        for m in messages:
          if 'subtype' not in m:  # ignore bot messages, join messages, etc.
            words = m['text'].split()
            if words:  # can have a msg w/o text, e.g. an uploaded image
              self.add_words_to_vocab(words)
        if history['has_more']:
          cursor = history['response_metadata']['next_cursor']
        else:
          break
        time.sleep(1.2)  # slack rate limit (max 50 history calls per minute)
    
    with open(self.vocab_file, 'w') as f:
      f.write(str(self.dict))
    
    self.inform_update_end(response)
  
  def sanitize(self, msg):
    """prevent bot from @mentioning people (distracting/annoying)"""
    msg = msg.replace("<!here>", "@here")
    msg = msg.replace("<!channel>", "@channel")
    msg = msg.replace("<!everyone>", "@everyone")
    for uid in self.user_id_to_name:
      msg = msg.replace(f"<@{uid}>", f"@{self.user_id_to_name[uid]}")
    return msg
  
  def gen(self):
    if not self.dict:
      with open(self.vocab_file, 'r') as f:
        self.dict = literal_eval(f.read())
    
    output = []
    inputs = (None, None)
    while True:
      if random.random() <= BIGRAM_WEIGHT and inputs in self.dict:
        word = random.choice(self.dict[inputs])
      else:
        word = random.choice(self.dict[inputs[1]])
      if word is None:
        break
      inputs = (inputs[1], word)
      output.append(word)
    return self.sanitize(' '.join(output))
  
  def post(self, msg, channel, to_user=None):
    return self.cli.api_call("chat.postMessage",
      channel=channel,
      text=msg,
      as_user=True)
  
  def is_command(self, output):
    try:
      assert output['type'] == 'message'
      text = output.get('text', '').upper()
      assert f"<@{self.bot_id}>" in text or self.bot_name.upper() in text
      assert output['user'] != self.bot_id
      return True
    except AssertionError:
      return False
  
  def run(self, recovered_traceback):
    print('Running')
    if recovered_traceback:
      self.post(recovered_traceback, DIAGNOSTIC_CHANNEL)
    while True:
      # heroku ephemeral file support: if vocabulary doesn't exist, create it
      if not os.path.isfile(self.vocab_file):
        self.update_dict()
      for output in self.cli.rtm_read():
        if self.is_command(output):
          self.post(self.gen(), output['channel'], output['user'])
      time.sleep(1)


if __name__ == '__main__':
  # on crash, wait a little then reconnect the bot
  recovered_traceback = None
  while True:
    try:
      SimulatorBot().run(recovered_traceback)
    except (slackclient.server.SlackConnectionError, websocket._exceptions.WebSocketException):
      # happens at random, unavoidable, don't bother saving the stack trace
      time.sleep(1)
    except Exception:
      # 'actual' problem; save and post it upon reconnecting
      traceback.print_exc()
      recovered_traceback = traceback.format_exc()
      time.sleep(1)

