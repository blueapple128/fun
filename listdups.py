import os
from sha256 import sha256
from collections import defaultdict

"""
Given an arbitrarily large and deep directory, output all files that are
duplicates of each other in that directory.
"""

# global
done = 0
found = 0

size_to_files = defaultdict(list)
hash_to_files = defaultdict(list)
hash_to_size = {}

def e(err):
  global done
  done += 1

def main():
  LOCATION = raw_input('Location: ')
  
  try:
    for root, dirs, files in os.walk(LOCATION, onerror=e):
      found += len(dirs)
      print '[', done, '/', found, '/', len(files), ']'
      done += 1
      
      i = 0
      while i < len(dirs):
        if dirs[i].startswith('.'):
          dirs.remove(dirs[i])
        else:
          i += 1

      for name in files:
        if name.startswith('.'):
          continue
        
        filename = os.path.join(root, name)

        try:
          files_of_size = size_to_files[os.stat(filename).st_size]
          files_of_size.append(filename)
          if len(files_of_size) > 1:
            if len(files_of_size) == 2:
              hash0 = sha256(files_of_size[0])
              hash_to_files[hash0].append(files_of_size[0])
            hash = sha256(filename)
            hash_to_files[hash].append(filename)
            if len(hash_to_files[hash]) > 1:
              hash_to_size[hash] = os.stat(filename).st_size
        except (IOError, WindowsError):
          pass

  except KeyboardInterrupt:
    pass

  with open('fooo.txt', 'w') as f:
    print '\n====='
    hash_to_size = hash_to_size.items()
    hash_to_size.sort(key=lambda t: -t[1])
    for hash, size in hash_to_size:
      print size, hash
      print hash_to_files[hash]
      f.write(str(size) + ' ' + hash + '\n')
      f.write(str(hash_to_files[hash]) + '\n')

if __name__ == '__main__':
  main()
