#
# Copyright (c) Elliot Peele <elliot@bentlogic.net>
#

import os
import sys
import shutil
import logging

import epdb
sys.excepthook = epdb.excepthook()

log = logging.getLogger('recover_copy')

def setupLogging(level=logging.INFO):
    rootLog = logging.getLogger('')
    streamHandler = logging.StreamHandler(sys.stderr)
    streamFormatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s')
    streamHandler.setFormatter(streamFormatter)
    rootLog.addHandler(streamHandler)
    rootLog.setLevel(level)
    return rootLog


class ErrorLogger(object):
    def __init__(self, fn):
        self._fh = open(fn, 'a')

    def error(self, path, msg):
        self._fh.write('%s %s\n' % (path, msg))
        log.error('Error copying %s - %s', path, msg)

    def close(self):
        self._fh.close()


class CopyAction(object):
    elog = ErrorLogger('copyerrors.log')

    def __init__(self, src, dest):
        self.src = src
        self.dest = dest

    def run(self):
        self._mkdestPath(self.dest)
        try:
            log.info('prepairing to copy %s -> %s', self.src, self.dest)
            shutil.copy2(self.src, self.dest)
            log.info('copying %s -> %s', self.src, self.dest)
        except (OSError, IOError) as e:
            self.elog.error(self.src, str(e))

    def _mkdestPath(self, path):
        d = os.path.dirname(path)
        if not os.path.exists(d):
            try:
                os.makedirs(path)
            except os.error as why:
                self.elog.error(self.src, str(why))


class Walker(object):
    def __init__(self, src_root, dest_root):
        self.src_root = os.path.abspath(src_root)
        self.dest_root = os.path.abspath(dest_root)

    def walk(self):
        for root, dirs, files in os.walk(self.src_root):
            actions = []

            if root.startswith(self.src_root):
                base_path = root[len(self.src_root)+1:]
            else:
                base_path = root
            log.debug('base_path: %s, root %s, src_root: %s', base_path, root,
                    self.src_root)

            for f in files:
                src = os.path.join(self.src_root, base_path, f)
                dest = os.path.join(self.dest_root, base_path, f)
                if os.path.exists(dest):
                    log.info('already copied %s' % src)
                    continue
                actions.append(CopyAction(src, dest))
            yield actions


class Copier(object):
    def __init__(self, src_root, dest_root):
        self.walker = Walker(src_root, dest_root)

    def copy(self):
        for actions in self.walker.walk():
            for action in actions:
                log.debug('trying to copy %s -> %s', action.src, action.dest)
                action.run()


def recovertree(src_root, dest_root):
    Copier(src_root, dest_root).copy()


if __name__ == '__main__':
    setupLogging(logging.INFO)
    src_root = sys.argv[1]
    dest_root = sys.argv[2]
    recovertree(src_root, dest_root)
