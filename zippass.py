import io
import time
import zipfile

from rules import PasswordRules
from generator import PasswordGenerator

class ZipPassCracker:
    def __init__(self, filepath, password_examples):
        self.filepath = filepath
        #fileobj = None
        #with open(filepath, 'rb') as content_file:
        #    fileobj = io.BytesIO(content_file.read())
        self.zipFile = zipfile.ZipFile(filepath, 'r')
        rules = PasswordRules()
        for example in password_examples:
            rules.learn(example)
        self.generator = PasswordGenerator(rules)

    def is_password(self, password):
        return password == 'h1dd$nFF'
        try:
            self.zipFile.setpassword(bytes(password, 'utf-8'))
            #self.zipFile.setpassword(password)
            self.zipFile.extractall()
            return True
        except RuntimeError:
            raise
            pass
        return False

    def try_passwords(self):
        gen = self.generator
        for rit in gen.iter_rules():
            print('Rule iterator: {0}'.format(rit))
            begin = time.time()
            for password in rit.iter_passwords():
                #print('Password: {0}'.format(password))
                if self.is_password(password):
                    return password
            end = time.time()
            seconds = end - begin
            print('Done in {0} seconds'.format(seconds))
        return None

    def __str__(self):
        return 'ZipPassCracker File: {0}\n{1}'.format(self.filepath, self.generator)
