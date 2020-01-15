r1_hashes = Hash.new

duplicates = 0

`ls RECOVERY_1`.split.each.with_index do |dir, i|
  `md5sum RECOVERY_1/#{dir}/*`.split("\n").each do |line|
    if r1_hashes.key?(line.split.first)
      duplicates += 1
    else
    	r1_hashes[line.split.first] = line.split.last
    end
  end
  print "#{i} "
end
puts "\nduplicates = #{duplicates}"

puts "r1_hashes has size #{r1_hashes.size}"

matches = 0
no_matches = 0

`ls RECOVERY_2`.split.each.with_index do |dir, i|
  `md5sum RECOVERY_2/#{dir}/*`.split("\n").each do |line|
    if r1_hashes.key?(line.split.first)
      wutface = "rm #{line.split.last}"
      if wutface.start_with? "rm RECOVERY_2"
        `#{wutface}`
      else
				puts wutface
        raise "AAAAAA"      
			end
    end
  end
  print "#{i} "
end
puts ""

