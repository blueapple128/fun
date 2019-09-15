import hashlib


def sha256(fname):
  """
  Quick helper to programmatically get the sha256 of an arbitrarily large file.
  """
  hash = hashlib.sha256()
  with open(fname, "rb") as f:
    while True:
      chunk = f.read(1048576)
      if not chunk:
        break
      hash.update(chunk)
  return hash.hexdigest()


if __name__ == '__main__':
  print sha256(raw_input('Filepath: '))
