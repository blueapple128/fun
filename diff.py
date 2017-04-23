import itertools
import os
from sha256 import sha256

"""
Given two directories of arbitrary size and depth, output all files that are
different between the two directories. Use for all those cases where folders
may have been duplicated in the past and now have diverged. Alternatively, use
to compress multiples of manual backups.
"""

DELETE = True

def gena(old_location):
  for root,dirs,files in os.walk(old_location):
    dirs.sort()
    files.sort()
    for file in files:
      yield os.path.join(root, file)[len(old_location):]


def genb(new_location):
  progress = 0
  for root,dirs,files in os.walk(new_location):
    dirs.sort()
    files.sort()
    for file in files:
      yield os.path.join(root, file)[len(new_location):]
    progress += 1
    if progress % 100 == 0:
      print progress,


def delete_if_match(old_file, new_file):
  try:
    if sha256(old_file) == sha256(new_file):
      if DELETE:
        os.remove(old_file)
    else:
      print "Changed:", old_file, new_file
  except (WindowsError, IOError) as e:
    print e


def main(old_location, new_location):
  x = gena(old_location)
  y = genb(new_location)
  prev_x = None
  prev_y = None

  diff_x = []
  diff_y = []

  mid_conflict = False
  mid_conflict_x = []
  mid_conflict_y = []
  mid_conflict_x_inv_ind = {}
  mid_conflict_y_inv_ind = {}

  try:
    while True:
      x, prev_x = itertools.tee(x)
      y, prev_y = itertools.tee(y)
      
      try:
        a = x.next()
      except StopIteration:
        a = ''
      try:
        b = y.next()
      except StopIteration:
        b = ''
      
      if a == '' and b == '' and not mid_conflict:
        break

      if a == b and not mid_conflict:
        delete_if_match(old_location + a, new_location + b)
        continue

      if not mid_conflict:
        mid_conflict = True
        saved_x = prev_x
        saved_y = prev_y

      mid_conflict_x.append(a)
      mid_conflict_y.append(b)
      mid_conflict_x_inv_ind[a] = len(mid_conflict_x) - 1
      mid_conflict_y_inv_ind[b] = len(mid_conflict_y) - 1

      if a in mid_conflict_y_inv_ind:
        pos = mid_conflict_y_inv_ind[a]
        diff_x.extend(mid_conflict_x[:-1])
        diff_y.extend(mid_conflict_y[:pos])
        y = saved_y
        while True:
          try:
            thing = y.next()
          except StopIteration:
            thing = ''
          if thing == a:
            break
        mid_conflict = False
        delete_if_match(old_location + mid_conflict_x[-1], new_location + mid_conflict_y[pos])
      elif b in mid_conflict_x_inv_ind:
        pos = mid_conflict_x_inv_ind[b]
        diff_x.extend(mid_conflict_x[:pos])
        diff_y.extend(mid_conflict_y[:-1])
        x = saved_x
        while True:
          try:
            thing = x.next()
          except StopIteration:
            thing = ''
          if thing == b:
            break
        mid_conflict = False
        delete_if_match(old_location + mid_conflict_x[pos], new_location + mid_conflict_y[-1])

      if not mid_conflict:
        mid_conflict_x = []
        mid_conflict_y = []
        mid_conflict_x_inv_ind = {}
        mid_conflict_y_inv_ind = {}
  except KeyboardInterrupt:
    pass

  with open('x.txt', 'w') as f:
    for item in diff_x:
      f.write(item + '\n')
  with open('y.txt', 'w') as f:
    for item in diff_y:
      f.write(item + '\n')


if __name__ == '__main__':
  main(raw_input('Old Location: '), raw_input('New Location: '))
