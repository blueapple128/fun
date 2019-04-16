from slackclient import SlackClient
import random
from ast import literal_eval
import os
import time
import traceback

BOT_TOKEN = os.environ['SIMULATORBOT_TOKEN']
SEARCH_TOKEN = os.environ['SIMULATORBOT_SEARCH_TOKEN']
WHITELISTED_NONPUBLIC_CHANNELS = (
  os.environ['WHITELISTED_NONPUBLIC_CHANNELS'].split(',')
)


class SimulatorBot:
  def __init__(self):
    self.cli = SlackClient(BOT_TOKEN)
    assert self.cli.rtm_connect()
    auth = self.cli.api_call("auth.test")
    self.bot_id = auth['user_id']
    self.bot_name = auth['user']
    self.vocab_file = f"{auth['team']}.vocab"
    self.dict = {}
  
  def update_dict(self):
    print('Updating...')
    # todo: time will vary depending on number of channels in the workspace and
    # number of messages in the channel
    response = self.post('Diagnostic message: Currently updating vocab file, bot will be down for about 30 seconds', "#random")
    self.dict = {None: []}
    
    cli2 = SlackClient(SEARCH_TOKEN)
    assert cli2.rtm_connect()
    
    # todo: pagination-insensitive API call assumes there are no more than 100
    # channels; works for this workspace but may not work for other workspaces
    channels = cli2.api_call(
      "conversations.list",
      types="public_channel,private_channel,mpim,im")['channels']
    channel_ids = [
      c['id']
      for c in channels
      if c['id'].startswith('C') or c['id'] in WHITELISTED_NONPUBLIC_CHANNELS
    ]
    
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
    
    print('Update done.')
    self.cli.api_call("chat.delete",
      channel=response['channel'],
      ts=response['ts'])
  
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
    return ' '.join(output)
  
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
  
  def run(self, crash_count, recovered_traceback):
    print('Running')
    if recovered_traceback:
      self.post(recovered_traceback, "#random")
      n_crashes = "1 crash" if crash_count == 1 else f"{crash_count} crashes"
      self.post(f"{self.bot_name} has auto-recovered from {n_crashes}",
        "#random")
    while True:
      # heroku ephemeral file support: if vocabulary doesn't exist, create it
      if not os.path.isfile(self.vocab_file):
        self.update_dict()
      for output in self.cli.rtm_read():
        if self.is_command(output):
          self.post(self.gen(), output['channel'], output['user'])
      time.sleep(1)


if __name__ == '__main__':
  # on unavoidable crash (e.g. ConnectionError), reboot and reconnect the bot,
  # saving the stack trace so the bot can post it upon reconnecting
  crash_count = 0
  recovered_traceback = None
  while True:
    try:
      SimulatorBot().run(crash_count, recovered_traceback)
    except Exception:
      traceback.print_exc()
      recovered_traceback = traceback.format_exc()
      crash_count += 1
      time.sleep(1)

