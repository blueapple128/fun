# Context: 
# Apartment wi-fi is suboptimal and cuts out at arbitrary times, but cycling
# airplane mode once fixes it until the next time it cuts out. If airplane mode
# is not cycled after a cut, the connection never comes back. Intervals between
# cuts arbitrarily range from hours to under 10 seconds. Not sure why it behaves
# so strangely, but this is just a quick script to detect connection cuts and
# autocycle airplane mode.

loop do
  out = `ping github.com -c 1 -w 1`
  if out.empty?
    puts 'Enabling airplane mode'
    `nmcli r all off`
    sleep 1
    puts 'Disabling airplane mode'
    `nmcli r all on`
    sleep 6
    puts 'Retrying'
  else
    print '.'
  end
  sleep 3
end

