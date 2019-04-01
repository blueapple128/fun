"""
Simulation script for the distance-vector routing protocol coded for
CS 4450 (Introduction to Computer Networks). Written proactively (not as a
class requirement!) from a desire to understand various race conditions in the
protocol better. Was done fast during spare time for personal use and thus
contains some hacks and ad-hoc code changes.
"""

from pprint import pprint as pp

INFINITY = 999999999  # convenience hack

def empty_inbox():
  return {'A': [], 'B': [], 'C': [], 'D': [], 'E': [], 'F': []}

def nnd(neighbors, source):
  """neighbors not down"""
  return [neighbor_dest for neighbor_dest in neighbors[source] if neighbors[source][neighbor_dest] != INFINITY]

def send(neighbors, tables, source, inbox, sent, outbox):
  """Modifies inbox and outbox."""
  for neighbor_dest in nnd(neighbors, source):
    # poisoned reverse
    # sending (A,5,B) to C
    # B tells C "I can get to A at cost 5"
    # but not if B relies on C to get to A!
    # B (source) to A (sent[0]) relies on C
    if tables[source][sent[0]][1] == neighbor_dest:
      inbox[neighbor_dest].append((sent[0], INFINITY, sent[2]))
    else:
      inbox[neighbor_dest].append(sent)
  outbox.append(sent)

def propagate(neighbors, tables, inbox, verbose=False):
  """Modifies tables (multiple times). Does not modify inbox (pointless)."""
  while True:
    new_inbox, _ = propagate_once(neighbors, tables, inbox, verbose)
    if verbose:
      print()
    if new_inbox == empty_inbox():
      break
    inbox = new_inbox

def propagate_once(neighbors, tables, inbox, verbose=False):
  """Modifies tables in place. Returns a new inbox."""
  did_update = False
  vprint = print if verbose else lambda x: None
  new_inbox = empty_inbox()
  for source in neighbors:
    if not inbox[source]:
      continue
    vprint('%s hears %s' % (source, s(inbox[source])))
    current_table_rows = []
    for faraway_dest in tables[source]:
      cost, next_hop = tables[source][faraway_dest]
      current_table_rows.append([faraway_dest, cost, next_hop])
    vprint('%s currently has table rows %s' % (source, s(current_table_rows)))
    calculated_table_rows = []
    for faraway_dest, cost, next_hop in inbox[source]:
      cost = min(INFINITY, cost + neighbors[source][next_hop])
      #!
      cost = cost + neighbors[source][next_hop]
      if cost > 320:
        cost = INFINITY
      #!
      calculated_table_rows.append([faraway_dest, cost, next_hop])
    vprint('%s considers prospective table rows %s' % (source, s(calculated_table_rows)))
    must_update_table_rows = []
    for faraway_dest, cost, next_hop in calculated_table_rows:
      current_cost, current_next_hop = tables[source][faraway_dest]
      if next_hop == current_next_hop and current_cost != cost:
        must_update_table_rows.append([faraway_dest, cost, next_hop])
        tables[source][faraway_dest] = [cost, next_hop]
    if must_update_table_rows:
      vprint('%s must use updated table rows %s' % (source, s(must_update_table_rows)))
      outbox = []
      for faraway_dest, cost, next_hop in must_update_table_rows:
        vprint('UPDATE: %s\'s path to %s is now cost %s through %s' % (source, faraway_dest, cost, next_hop))
        did_update = True
        sent = (faraway_dest, cost, source)
        send(neighbors, tables, source, new_inbox, sent, outbox)
      #vprint('%s sends %s to %s' % (source, s(outbox), s(nnd(neighbors, source))))
      # refresh current table rows var in the background
      current_table_rows = []
      for faraway_dest in tables[source]:
        cost, next_hop = tables[source][faraway_dest]
        current_table_rows.append([faraway_dest, cost, next_hop])
    # source picks best options among calculated and current table rows
    candidate_rows = calculated_table_rows + current_table_rows
    # patch to extra check neighbors
    #candidate_rows += [[n, neighbors[source][n], n] for n in neighbors[source]]
    #
    outbox = []
    for faraway_dest in tables[source]:
      one_row_candidates = [r for r in candidate_rows if r[0] == faraway_dest]
      _dest, best_cost, best_next_hop = sorted(sorted(one_row_candidates, key=lambda dcn: dcn[2]), key=lambda dcn: dcn[1])[0]
      vprint('%s picks %s as the best among %s' % (source, s([faraway_dest, best_cost, best_next_hop]), s(one_row_candidates)))
      if tables[source][faraway_dest] != [best_cost, best_next_hop]:
        tables[source][faraway_dest] = [best_cost, best_next_hop]
        vprint('UPDATE: %s\'s path to %s is now cost %s through %s' % (source, faraway_dest, best_cost, best_next_hop))
        did_update = True
        sent = (faraway_dest, best_cost, source)
        send(neighbors, tables, source, new_inbox, sent, outbox)
    #vprint('%s sends %s to %s' % (source, s(outbox), s(nnd(neighbors, source))))
  if verbose:
    pp(tables)
  return new_inbox, did_update


def update(neighbors, tables, verbose=False, first=True):
  """Returns new inbox to be passed to propagate. Does not modify tables."""
  vprint = print if verbose else lambda x: None
  inbox = empty_inbox()
  for source in neighbors:
    outbox = []
    # source tells neighbor-dests about faraway-dests that source knows
    for faraway_dest in tables[source]:
      if first or faraway_dest != source:
        cost, _next_hop = tables[source][faraway_dest]
        sent = (faraway_dest, cost, source)
        send(neighbors, tables, source, inbox, sent, outbox)
    vprint('%s sends %s to %s' % (source, s(outbox), s(nnd(neighbors, source))))
  return inbox

def failure(neighbors, tables, failure_pair, verbose=False):
  """Modifies neighbors and tables. Returns inbox of new messages."""
  vprint = print if verbose else lambda x: None
  
  x,y = failure_pair
  # intentional throw (KeyError) if x and y aren't neighbors
  neighbors[x][y] = INFINITY
  neighbors[y][x] = INFINITY
  vprint('Failure: link between %s and %s broken!' % failure_pair)
  
  inbox = empty_inbox()
  for source, broken_neighbor in [(x,y), (y,x)]:
    outbox = []
    for faraway_dest in tables[source]:
      _unused_cost, next_hop = tables[source][faraway_dest]
      if next_hop == broken_neighbor:
        tables[source][faraway_dest] = [INFINITY, '-']
        vprint('UPDATE: %s\'s path to %s is now infinite' % (source, faraway_dest))
        # source notifies all neighbors of failure, except broken neighbor_dest
        sent = (faraway_dest, INFINITY, source)
        send(neighbors, tables, source, inbox, sent, outbox)
    #vprint('%s sends %s to %s' % (source, s(outbox), s(nnd(neighbors, source))))
  return inbox

def s(m):
  """hack convenience function for converting things to nicer strings than
  the default
  e.g. "(A,1,B)" instead of "('A', 1, 'B')" or "[A,B]" instead of "['A', 'B']"
  """
  if type(m) == list:
    return '[' + ','.join([s(item) for item in m]) + ']'
  elif type(m) == tuple and len(m) == 3:
    return '(%s,%s,%s)' % m
  elif type(m) == dict:
    return s(list(m.keys()))
  elif type(m) == int or type(m) == str:
    return '%s' % m
  else:
    raise

NETWORK = {
  'A': {'B': 2, 'C': 1},
  'B': {'A': 2, 'C': 7},
  'C': {'A': 1, 'B': 7},
}

neighbors = NETWORK

fail_pair = ('C', 'B')

tables = {}

for source in neighbors:
  tables[source] = {}
  for dest in neighbors:
    if source == dest:
      tables[source][dest] = [0, '-']
    else:
      tables[source][dest] = [INFINITY, '-']

inbox = update(neighbors, tables, first=True)
propagate(neighbors, tables, inbox)

# Now t=0 and the fun begins

inboxes = [None for _ in range(100)]

if False:
  # race
  temp_inbox1 = update(neighbors, tables, verbose=True)
  temp_inbox2 = failure(neighbors, tables, fail_pair, verbose=True)
  # merge inboxes together properly and store in inboxes[1]
  inbox_dict = {}
  # make sure temp_inbox1 takes priority over temp_inbox2
  for neighbor_dest in temp_inbox2:
    inbox_dict[neighbor_dest] = {}
    ref = inbox_dict[neighbor_dest]
    for faraway_dest, cost, source in temp_inbox2[neighbor_dest]:
      if faraway_dest not in ref:
        ref[faraway_dest] = {}
      ref[faraway_dest][source] = cost  # :grimacing:
  for neighbor_dest in temp_inbox1:
    ref = inbox_dict[neighbor_dest]
    for faraway_dest, cost, source in temp_inbox1[neighbor_dest]:
      if faraway_dest not in ref:
        ref[faraway_dest] = {}
      ref[faraway_dest][source] = cost
  inboxes[1] = empty_inbox()
  for neighbor_dest in inbox_dict:
    for faraway_dest in inbox_dict[neighbor_dest]:
      for source in inbox_dict[neighbor_dest][faraway_dest]:
        cost = inbox_dict[neighbor_dest][faraway_dest][source]
        inboxes[1][neighbor_dest].append((faraway_dest, cost, source))
failure(neighbors, tables, fail_pair, verbose=True)
#inboxes[1] = update(neighbors, tables, verbose=True)

pp(tables)
print()

magic = INFINITY

for i in range(0, len(inboxes)):
  if inboxes[i] == empty_inbox() and i > 0:
    break
  print('Starting t=%s:' % i)
  if i%1 == 0:
    inboxes[i] = update(neighbors, tables, verbose=True)
    temp_inbox, did_update = propagate_once(neighbors, tables, inboxes[i], verbose=True)
    #for source in inboxes[i+1]:
    #  inboxes[i+1][source].extend(temp_inbox[source])
  else:  
    inboxes[i+1] = propagate_once(neighbors, tables, inboxes[i], verbose=True)
  print()
  if not did_update and magic == INFINITY:
    magic = i
  if i == magic + 0:
    break

