import os
from listdups import get_duplicates


def double_os_walk(location1, location2):
  for root, dirs, files in os.walk(location1):
    yield root, dirs, files
  for root, dirs, files in os.walk(location2):
    yield root, dirs, files

def main(delete_dir, check_dir):
  """
  Deletes all files in `delete_dir` that can already be found in `check_dir`
  (are duplicates of files in `check_dir`).
  """
  duplicates = get_duplicates(double_os_walk(delete_dir, check_dir))
  
  for one_set_of_duplicates in duplicates.values():
    # given a set of files that are duplicates of each other,
    # IF at least one file in the set is in `check_dir`,
    # delete all files in the set that are in `delete_dir`.
    if any([file.startswith(check_dir) for file in one_set_of_duplicates]):
      for file in one_set_of_duplicates:
        if file.startswith(delete_dir):
          os.remove(file)


if __name__ == '__main__':
  delete_dir = raw_input('Delete files from: ')
  check_dir = raw_input('that are duplicates of files in: ')
  main(unicode(delete_dir), unicode(check_dir))
