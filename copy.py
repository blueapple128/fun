import os
import shutil


# Scans the old_location beforehand to enumerate its files and be able to
# display an exact progress bar. Slower.
SHOW_PROGRESS = True


def copy(old_location, new_location):
  """
  Copy everything from old_location to new_location, automatically ignoring
  (and outputting) all errors. Intended to be used on deep system-level
  directories and the like, where the OS may be expected to throw many
  ignorable errors that the user would otherwise have to manually wait and
  click through for hours (such as copying a file that no longer exists or
  attempting to copy a file that the Administrator does not have permission to
  access (thanks, Windows)). Trades off speed for automation.
  """
  if SHOW_PROGRESS:
    print "Scanning..."
    num_files = 0
    for root, dirs, files in os.walk(old_location):
      num_files += len(files)
      print num_files,
    copied_files = 0
  
  if not os.path.exists(new_location):
    try:
      os.mkdir(new_location)
    except (WindowsError) as e:
      print e
  
  print "\nCopying..."
  
  for root, dirs, files in os.walk(old_location):
    for dir in dirs:
      new_dir = os.path.join(new_location + root[len(old_location):], dir)
      if not os.path.exists(new_dir):
        try:
          os.mkdir(new_dir)
        except (WindowsError) as e:
          print e
    for file in files:
      new_file = os.path.join(new_location + root[len(old_location):], file)
      if not os.path.exists(new_file):
        try:
          shutil.copyfile(os.path.join(root, file), new_file)
        except (IOError) as e:
          print e
      if SHOW_PROGRESS:
        copied_files += 1
        print "[" + str(copied_files) + "/" + str(num_files) + "]",


if __name__ == '__main__':
  copy(raw_input('Old Location: '), raw_input('New Location: '))
