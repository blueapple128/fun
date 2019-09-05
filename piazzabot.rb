require 'slack-ruby-client'

BOT_TOKEN = ENV['PIAZZABOT_TOKEN']

Slack.configure do |config|
  config.token = BOT_TOKEN
end

$cl = Slack::RealTime::Client.new

def start_with_retry!
  loop do
    begin
      $cl.start!
      break
    rescue StandardError
      sleep 15
      puts "Retrying at #{Time.now}"
    end
  end
end

$cl.on :hello do
  puts "Running"
  $botid = $cl.self.id
  $botname = $cl.self.name
end

def invalid?(data)
  (data.nil? || data.text.nil? || data.user.nil? || data.channel.nil?)
end

def msg(channel, text)
  $cl.web_client.chat_postMessage channel: channel, text: text, as_user: false, username: "campuswirebot"
end

$cl.on :message do |data|
  begin
    next if invalid?(data)
    
    match = /(?:^|\W)#(\d{1,4})\b/.match(data.text)
    if match
      msg(data.channel, "https://campuswire.com/c/G8FE6D09F/feed/#{match[1]}")
    end
  rescue StandardError => e
    exception = ([e.inspect] + e.backtrace.select { |line| !line.include? ".rvm" }).join("\n")
    msg(data.channel, "<@U5G7Z8NM9> #{exception}")
  end
end

$cl.on :close do
  puts "Closing"
end

$cl.on :closed do
  puts "Closed"
  start_with_retry!
end

start_with_retry!
