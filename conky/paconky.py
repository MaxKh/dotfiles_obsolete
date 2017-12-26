#!/usr/bin/env python3
# -*- coding: utf8 -*-

# Author: Xyne
# Updated: MaxKh

"""Display information about upgradable packages in Conky.

This script is meant to be customized. The default is just an example.

USAGE
  paconky /temporary/database/path [sync command]

EXAMPLES
  A static path:

      paconky ~/.cache/pacman

  Using tmpfs:

      paconky /dev/shm/pacman

  If the XDG_CACHE_HOME variable is set with 1 path:

      paconky "$XDG_CACHE_HOME"/pacman

  ... or with multiple paths:

      paconky "$(echo $XDG_CACHE_HOME | cut -d':' -f1)"/pacman

  The sync command will replace '%d' with the sync database directory and '%r'
  with the database root. This can be used to invoke powerpill for syncing
  the databases:

      paconky /tmp/paconky powerpill -b '%r' -Sy


DEPENDENCIES
  * pyalpm
  * python3-aur


EXAMPLE CONKY CONFIGURATION FILE

  alignment top_left
  gap_x 5
  gap_y 0
  maximum_width 200
  minimum_size 200,1
  own_window yes
  own_window_transparent yes
  own_window_type override
  own_window_hints below

  update_interval 3600
  total_run_times 0
  double_buffer yes

  use_xft yes
  xftfont lime:pixelsize=10
  xftalpha 0.9

  default_color ff0000
  default_outline_color black
  default_shade_color black

  uppercase no
  override_utf8_locale no

  text_buffer_size 4096

  color1 444444
  color2 cccccc
  color3 777777


  TEXT
  ${execp /path/to/paconky /tmp/paconky}



"""

import AUR.RPC as AUR
import errno
import glob
import os
import pyalpm
import shutil
import subprocess
import sys
import urllib.error

from collections import OrderedDict
from pycman import config, action_sync, transaction

def display(upgradable_sync, upgradable_aur):
  """Display the output.

  upgradable_sync: An OrderedDict of sync database names and sets of tuples.
  Each tuple consists of the local package and sync package returned by pyalpm.

  upgradable_aur: A list of tuples. Each tuple consists of the local package
  returned by pyalpm and a dictionary object returned from the AUR.
  """

  # To change the output, edit these formatting strings.
  # You can change anything except the number of "%s" in each.
  # If you need to insert a percent sign, use "%%".
  # The header at the top of each repo list.
  header = '${color1}${hr}\n${color1}[${color2}%s${color1}] ${alignr}${color3}%s'
  error = 'update check failed'
  zero = 'updated'
  one = '1 new package'
  many = '%d new packages'
  # Text shown instead of repo when everything is up-to-date.
  zero_text = 'local packages'

  # The line showing a package and the available version.
  line = '\n${color1}%s ${alignr}%s'

  # The footer at the end of the list.
  footer = '\n${color1}${hr}\n \n '

  h = config.init_with_config("/etc/pacman.conf")

  # An error occured.
  if upgradable_sync is None or upgradable_aur is None:
    print(header % (zero_text, error) + footer);

  # Nothing to upgrade.
  elif not (upgradable_sync or upgradable_aur):
    print(header % (zero_text, zero) + footer);

  else:
    for repo, pkgs in upgradable_sync.items():
      n = len(pkgs)
      if n > 1:
        msg = many % n
      else:
        msg = one

      print(header % (repo,msg), end='');

      pkgs = sorted(pkgs, key=lambda x: x[0].name)
      for local, sync in pkgs:

        name, version = "", ""

        try:
          locked_group = set(local.groups) & set(h.ignoregrps)
          if local.name in h.ignorepkgs or len(locked_group):
            name, version = local.name, str(sync.version)+"${color2}/locked${color}"
          else:
            name, version = local.name, sync.version
        except:
          name, version = "alpm issue", "detected"

        if len(name) > 20:
          name = name[0:18] + "..."

        print(line % (name, version), end='')

      print(footer)


    if upgradable_aur:
      n = len(upgradable_aur)
      if n > 1:
        msg = many % n
      else:
        msg = one

      print(header % ('AUR',msg), end='');

      upgradable_aur.sort(key=lambda x: x['Name'])
      for pkg in upgradable_aur:
        print(line % (pkg['Name'], pkg['Version']), end='')

      print(footer)



def main(tmp_db_path, sync_cmd=None):
  # Use a temporary database path to avoid issues caused by synchronizing the
  # sync database without a full system upgrade.

  # See the discussion here:
  #   https://bbs.archlinux.org/viewtopic.php?pid=951285#p951285

  # Basically, if you sync the database and then install packages without first
  # upgrading the system (-y), you can do some damage.


  tmp_db_path = os.path.abspath(tmp_db_path)
#   conf = config.PacmanConfig(conf = '/etc/pacman.conf')
  h = config.init_with_config("/etc/pacman.conf")
  db_path = h.dbpath
  if tmp_db_path == db_path:
    print("temporary path cannot be %s" % db_path)
    sys.exit(1)
  local_db_path = os.path.join(db_path, 'local')
  tmp_local_db_path = os.path.join(tmp_db_path, 'local')

  # Set up the temporary database path
  if not os.path.exists(tmp_db_path):
    os.makedirs(tmp_db_path)
    os.symlink(local_db_path, tmp_local_db_path)
  elif not os.path.islink(tmp_local_db_path):
    # Move instead of unlinking just in case.
    if os.path.exists(tmp_local_db_path):
      sys.stderr.write(
        "warning: expected file or directory at %s\n" % tmp_local_db_path
      )
      i = 1
      backup_path = tmp_local_db_path + ('.%d' % i)
      while os.path.exists(backup_path):
        i += 1
        backup_path = tmp_local_db_path + ('.%d' % i)
      sys.stderr.write("attempting to move to %s\n" % backup_path)
      os.rename(tmp_local_db_path, backup_path)
    os.symlink(local_db_path, tmp_local_db_path)

  # Copy in the existing database files. If a repo is offline when paconky is
  # run then no database will be downloaded. If the databases are not copied
  # first then the output will be inconsistent due to missing information. For
  # example, if the Haskell repo is offline then Haskell packages will appear
  # in the [community] and [AUR] sections of the output.
  tmp_sync_db_path = os.path.join(tmp_db_path, 'sync')
  os.makedirs(tmp_sync_db_path, exist_ok=True)
  sync_db_path = os.path.join(db_path, 'sync')

  for db in glob.iglob(os.path.join(sync_db_path,'*.db')):
    tmp_db = os.path.join(tmp_sync_db_path, os.path.basename(db))
    try:
      mtime = os.path.getmtime(tmp_db)
    except OSError as e:
      if e.errno != errno.ENOENT:
        raise e
      else:
        mtime = 0
    if mtime < os.path.getmtime(db):
      shutil.copy2(db, tmp_db)



  # Sync the temporary database.
  # Support external synchronizers such as parisync.
  if sync_cmd:
    for index, item in enumerate(sync_cmd):
      if item == '%d':
        sync_cmd[index] = tmp_sync_db_path
      elif item == '%r':
        sync_cmd[index] = os.path.dirname(tmp_sync_db_path)
    p = subprocess.Popen(sync_cmd, stdout=subprocess.PIPE)
    e = p.wait()
    if e != 0:
      sys.stderr.write("sync command exited with %d\n" % e)
    # Re-initialize with new databases.
    args = action_sync.parse_options(('-b', tmp_db_path))
    h = config.init_with_config_and_options(args)
  else:
    args = action_sync.parse_options(('-b', tmp_db_path, '-y'))
    h = config.init_with_config_and_options(args)
    sys.stdout = sys.__stderr__
    try:
      t = transaction.init_from_options(h, args)
    except pyalpm.error as e:
      sys.stderr.write('%s\n' % (e,))
      eno = e.args[1]
      if eno == 10:
        lckpath = os.path.join(tmp_db_path, 'db.lck')
        sys.stderr.write('  %s\n' % lckpath)
      sys.exit(1)
    for db in h.get_syncdbs():
      try:
        db.update(False)
      except pyalpm.error as e:
        sys.stderr.write('%s: %s\n' % (db.name, e))
    t.release()
    sys.stdout = sys.__stdout__


  installed = set(p for p in h.get_localdb().pkgcache)
  upgradable = OrderedDict()

  syncdbs = h.get_syncdbs()
  for db in syncdbs:
    # Without "list" the set cannot be altered with "remove" below.
    for pkg in list(installed):
      pkgname = pkg.name
      syncpkg = db.get_pkg(pkgname)
      if syncpkg:
        if pyalpm.vercmp(syncpkg.version, pkg.version) > 0:
          try:
            upgradable[db.name].add((pkg, syncpkg))
          except KeyError:
            upgradable[db.name] = set(((pkg, syncpkg),))
        installed.remove(pkg)

  foreign = dict([(p.name,p) for p in installed])

  try:
    aur = AUR.AurRpc()
    aur_pkgs = aur.info(foreign.keys())
    upgradable_aur = list()
    for aur_pkg in aur_pkgs:
      try:
        installed_pkg = foreign[aur_pkg['Name']]
      except KeyError:
        upgradable_aur.append(aur_pkg)
        continue
      if pyalpm.vercmp(aur_pkg['Version'], installed_pkg.version) > 0:
        upgradable_aur.append(aur_pkg)
      installed.remove(installed_pkg)
  except AUR.AurError as e:
    sys.stderr.write(str(e))
    sys.exit(1)
  except urllib.error.URLError as e:
    sys.stderr.write(
      'error: failed to retrieve information from the AUR (%s)\n' % e.reason
    )
    upgradable_aur = None
  except TypeError:
    upgradable_aur = None


  display(upgradable, upgradable_aur)



if __name__ == "__main__":
  if sys.argv[1:]:
    main(sys.argv[1], sys.argv[2:])
  else:
    print("no temporary path given")
    sys.exit(1)
