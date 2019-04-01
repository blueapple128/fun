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
TXT_FILE = os.environ['SOURCE_TXT_FILE']


class SimulatorBot(object):
  def __init__(self, vocab_file):
    self.cli = SlackClient(BOT_TOKEN)
    assert self.cli.rtm_connect()
    self.bot_name = self.cli.api_call("users.info", user=BOT_ID)['user']['name']
    self.vocab_file = vocab_file
    self.counter = 0
    self.dict = {}
  
  def update_dict(self):
    self.dict = {None: []}
    
    cli2 = SlackClient(SEARCH_TOKEN)
    assert cli2.rtm_connect()
    pages = cli2.api_call("search.messages",
                          query="after:2012",
                          count=100)['messages']['paging']['pages']
    for p in range(1, pages+1):
      success = False
      while not success:
        print p, pages
        try:
          msgs = cli2.api_call("search.messages",
                              query="after:2012",
                              count=100,
                              page=p)['messages']['matches']
          success = True
          time.sleep(3)
        except Exception:
          pass
    
      for msg in msgs:
        words = msg['text'].split()
        try:
          self.dict[None].append(words[0])
        except IndexError:
          print `msg['text']`
        for i in range(len(words)):
          source_word = words[i]
          dest_word = words[i+1] if i+1 in range(len(words)) else None
          if source_word in self.dict:
            self.dict[source_word].append(dest_word)
          else:
            self.dict[source_word] = [dest_word]
    
    with open(self.vocab_file, 'w') as f:
      f.write(str(self.dict))
  
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
                 text=("<@" + to_user + "> " if to_user else "") + msg,
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
    try:
      while True:
        for output in self.cli.rtm_read():
          if self.is_command(output):
            self.post(self.gen(), output['channel'], output['user'])
        time.sleep(1)
        self.counter += 1
        if self.counter % 3600 == 0:
          self.update_dict()
          self.post(self.gen(), "#random")
    except Exception:
      traceback.print_exc()
      self.post(traceback.format_exc(), "#random")


if __name__ == '__main__':
  SimulatorBot(TXT_FILE).run()

