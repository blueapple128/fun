import os
from sha256 import sha256
from collections import defaultdict
from itertools import tee

"""
Given an arbitrarily large and deep directory, output all files that are
duplicates of each other in that directory, sorted from largest to smallest.

Uses SHA256 to check for duplicates and a (literal) hashtable of seen hashes in
order to run in O(n) instead of O(n^2).
"""

# When on, checks how many files there are in the directory first before
# beginning any work searching for duplicates. Trades speed for being able to
# display an accurate progress bar.
PROGRESS_BAR = True

# When on, ignores all files and directories whose name begins with '.' (acts
# as if they do not exist).
IGNORE_HIDDEN = True

def get_duplicates(generator):
  """`generator` should most likely be equal to os.walk(location) where
  location is the filesystem location/directory that is to be searched.
  Returns a list of filenames that are duplicates of each other inside the
  given location, indexed by a tuple of (filesize, hash).
  
  E.g.
  {
    (1024, 0x00000000deadbeef): [ <filenames with this hash> ],
    (1048576, 0xfedcba9876543210): [ <filenames with this hash> ],
  }
  """
  # intermediate vars (inverted indices)
  # debugging note: files listed in these structures aren't necessarily
  # duplicates; they just need to be kept track of on the search for duplicates
  size_to_files = defaultdict(list)
  hash_to_files = defaultdict(list)
  
  # final output (any files listed here are definitely duplicates)
  duplicates = defaultdict(list)
  
  if PROGRESS_BAR:
    generator, generator_copy = tee(generator)
    
    total_files = 0
    for root, dirs, files in generator_copy:
      if IGNORE_HIDDEN:
        total_files += len([f for f in files if not f.startswith('.')])
      else:
        total_files += len(files)
    searched_files = 0
  
  try:
    for root, dirs, files in generator:
      if IGNORE_HIDDEN:
        files = [f for f in files if not f.startswith('.')]
        # Must filter dirs in place; can't use filter()
        i = 0
        while i < len(dirs):
          if dirs[i].startswith('.'):
            dirs.remove(dirs[i])
          else:
            i += 1

      for name in files:
        # Tricky optimization:
        # Maintaining a map of hashes to files is the 'naive' O(n) solution,
        # but finding the SHA256 of a large file takes a while; directory may
        # have numerous large files but few of them will be duplicates. Since
        # files can only be duplicates if they're the same size, begin by
        # mapping only sizes to files; don't bother calculating hashes until
        # multiple files of the same size are found.
        
        # Example: Files A, B, C, and D are all the same size. After finding A,
        # store its size only. After finding B (and discovering that its size
        # matches A's), need to calculate the hash of *both* A and B. After
        # finding C (and discovering that its size has been seen before), need
        # to calculate the hash of (only) C. After finding D, need to calculate
        # the hash of (only) D.
        
        filename = os.path.join(root, name)
        size = os.stat(filename).st_size
        
        #try:
        files_of_this_size = size_to_files[size]
        files_of_this_size.append(filename)
        if len(files_of_this_size) >= 2:
          # size 'duplicate' found; need to know the hash of this file
          hash = sha256(filename)
          files_of_this_hash = hash_to_files[hash]
          files_of_this_hash.append(filename)
          if len(files_of_this_size) == 2:
            # need to know the hash of not just this file, but also the one
            # other file that had the same size
            hash0 = sha256(files_of_this_size[0])
            files_of_this_hash0 = hash_to_files[hash0]
            files_of_this_hash0.append(files_of_this_size[0])
          
          if len(files_of_this_hash) >= 2:
            # true duplicate found
            duplicates[(size, hash)] = files_of_this_hash
        
        #except (IOError, WindowsError):
        #  pass
        
      if PROGRESS_BAR:
        searched_files += len(files)
        print searched_files, '/', total_files

  except KeyboardInterrupt:
    pass
  
  return duplicates


def main(location):
  duplicates = get_duplicates(os.walk(location))
  
  # sort by decreasing size (convert dict to list of (key, value) pairs)
  duplicates = sorted(duplicates.items(), key=lambda kv: -kv[0][0])
  
  with open('listdups.txt', 'w') as f:
    for size_and_hash, filenames in duplicates:
      size, hash = size_and_hash
      f.write(str(size) + ' ' + hash + '\n')
      print size, hash
      for filename in filenames:
        f.write(filename + '\n')
        print filename
      f.write('\n')
      print

if __name__ == '__main__':
  main(unicode(raw_input('Location: ')))
