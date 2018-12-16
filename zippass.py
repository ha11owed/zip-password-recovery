import io
import time
import zipfile

from rules import PasswordRules
from generator import PasswordGenerator, PasswordVerifier


class ZipPassCracker(PasswordVerifier):
    """
    The python zip library is not really appropriate for the task:
    it can't work with all types of passwords and is too slow.
    """

    def __init__(self, filepath, password_examples):
        PasswordVerifier.__init__(self, password_examples, self.is_zip_password)
        self.filepath = filepath
        fileobj = None
        with open(filepath, 'rb') as content_file:
            fileobj = io.BytesIO(content_file.read())
        self.zipFile = zipfile.ZipFile(filepath, 'r')
        rules = PasswordRules()
        for example in password_examples:
            rules.learn(example)
        self.generator = PasswordGenerator(rules)

    def is_zip_password(self, password):
        try:
            self.zipFile.setpassword(password)
            self.zipFile.extractall()
            return True
        except RuntimeError:
            pass
        return False

    def __str__(self):
        return 'ZipPassCracker File: {0}\n{1}'.format(self.filepath, self.generator)
