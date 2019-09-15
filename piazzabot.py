import slackclient
import re
import websocket
import os
import time
import traceback

BOT_TOKEN = os.environ['PIAZZABOT_TOKEN']
DIAGNOSTIC_CHANNEL = "#_test"  # where to post update and crash recovery notices


class Piazzabot:
  def __init__(self):
    self.cli = slackclient.SlackClient(BOT_TOKEN)
    assert self.cli.rtm_connect()
    auth = self.cli.api_call("auth.test")
    self.bot_id = auth['user_id']
    self.bot_name = auth['user']

  def post(self, msg, channel):
    return self.cli.api_call("chat.postMessage",
      channel=channel,
      text=msg,
      as_user=False,
      username="campuswirebot")
  
  def run(self, recovered_traceback):
    print('Running')
    if recovered_traceback:
      self.post(recovered_traceback, DIAGNOSTIC_CHANNEL)
    while True:
      for output in self.cli.rtm_read():
        if output['type'] == 'message':
          m = re.search(r"(?:^|\W)#(\d{1,4})\b", output.get('text', ''))
          if m:
            self.post(f"https://campuswire.com/c/G8FE6D09F/feed/{m.group(1)}", output['channel'])
      time.sleep(1)


if __name__ == '__main__':
  # on crash, wait a little then reconnect the bot
  recovered_traceback = None
  while True:
    try:
      Piazzabot().run(recovered_traceback)
    except (slackclient.server.SlackConnectionError, websocket._exceptions.WebSocketException):
      # happens at random, unavoidable, don't bother saving the stack trace
      time.sleep(1)
    except Exception:
      # 'actual' problem; save and post it upon reconnecting
      traceback.print_exc()
      recovered_traceback = traceback.format_exc()
      time.sleep(1)

