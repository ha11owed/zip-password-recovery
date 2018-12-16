import os
import sys
import re
import time
import tempfile

from getpass import getpass
from subprocess import Popen, PIPE, STDOUT
from threading import Thread

def print_list(items):
    print('count: {0}'.format(len(items)))
    for item in items:
        print(' {0}'.format(item))

def print_args(args):
    print('Arguments:')
    for arg in vars(args):
        print('  {0}={1}'.format(arg, getattr(args, arg)))

class Helpers:
    def __init__(self):
        self._logfile = None
        self._logstream = None
        self._raw_input = raw_input

    def set_logfile(self, logfile):
        self.close()
        self._logfile = logfile
    
    def get_logstream(self):
        if self._logstream is None and self._logfile:
            self._logstream = open(self._logfile, 'a')
        return self._logstream

    def log(self, msg=''):
        while True:
            if msg is None:
                msg = '\n'
                break
            is_str = isinstance(msg, str)
            if not is_str:
                break
            if not msg.endswith('\n'):
                msg = msg + '\n'
            if '@' in msg:
                # obfuscate any strings that contain user/pass like: http://user:pass@domain/
                msg = re.sub('://.*@', '://[obfuscated]@', msg)
            break

        msg = '{0} {1}'.format(self._get_timestamp_str(), msg)
        logstream = self.get_logstream()
        if logstream is None:
            return
        logstream.write(msg)
        logstream.flush()

    def output(self, msg):
        self.log('# output: {0}'.format(msg))
        print(msg)

    def close(self):
        if self._logstream is None:
            return
        self._logstream.close()
        self._logstream = None

    def _get_timestamp_str(self):
        now = time.time()
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))

    def _run_redirect_thread(self, istream, ostreams):
        while True:
            buf = istream.read(1)
            if not buf:
                break

            for ostream in ostreams:
                ostream.write(buf)
            logstream = self.get_logstream()
            if logstream is not None:
                logstream.write(buf)

    def _create_redirect_thread(self, istream, ostreams):
        thread = Thread(target=self._run_redirect_thread,
                        args=(istream, ostreams, ))
        thread.start()
        return thread

    def pick_listitem(self, items, title=''):
        """Select an item from the given list"""
        index = 0
        for item in items:
            index += 1
            print(' {0} - {1}'.format(index, item))

        msg = 'Select {0}[1..{1}]: '.format(title, index)
        index = int(self._raw_input(msg).strip()) - 1
        result = None
        if index >= 0 and index < len(items):
            result = items[index]
        self.log('User picked: {0} from {1}'.format(result, ', '.join(items)))
        return result

    def pick(self, title, find_method, find_params):
        result = None
        index = 0
        while index < len(find_params):
            curr_params = find_params[index]
            msg_part = '{0} found for {1}.'.format(title, ', '.join(str(x) for x in curr_params))

            items = find_method(curr_params)
            if items is None or len(items) == 0:
                self.output('No ' + msg_part)
                index += 1
            elif len(items) > 1:
                self.output('Multiple ' + msg_part)
                result = self.pick_listitem(items, title)
            else:
                result = items[0]
            break
        return result

    def exec_cmd(self, cmd, pwd):
        """Execute a command and log its output to a log file"""
        if not os.path.exists(pwd):
            os.makedirs(pwd)

        # run the command and pipe both the out and err to the log, stdout and a temporary pipe.
        self.log("# exec_cmd: {0}. pwd={1}".format(' '.join(cmd), pwd))
        sys.stdout.flush()
        proc = Popen(cmd, cwd=pwd, stdout=PIPE, stderr=PIPE)
        #pcat = Popen([ 'cat' ], cwd=pwd, stdin=proc.stdout, stdout=PIPE)
        fout = tempfile.TemporaryFile()
        tout = self._create_redirect_thread(proc.stdout, [ sys.stdout, fout ])
        terr = self._create_redirect_thread(proc.stderr, [ sys.stdout, fout ])
        proc.wait()
        tout.join()
        terr.join()
        sys.stdout.flush()

        # result code
        self.log("# exec_cmd ended with result code {0}".format(proc.returncode))
        if proc.returncode != 0:
            raise Exception('Command {0} finished with error {1}'.format(cmd, proc.returncode))
        # return the output lines
        fout.seek(0)
        return fout.readlines()
