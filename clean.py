import os

def clean(location):
  """Delete purely empty directories accessible from location."""
  for root, dirs, files in os.walk(location, topdown=False):
    for dir in dirs:
      try:
        os.rmdir(os.path.join(root, dir))
      except WindowsError:
        pass  # not empty

if __name__ == '__main__':
  clean(raw_input('Location: '))
