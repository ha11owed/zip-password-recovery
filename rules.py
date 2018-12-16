
class RangeRule:
    """
    Represents a rule for the range of an element in a password.
    For example for the length of the password, the number of digits, etc...
    """

    def __init__(self):
        self.min = 1000000
        self.max = 0
    
    def restrict(self, value):
        """Expand the range to include the specified value"""
        self.min = min(self.min, value)
        self.max = max(self.max, value)

    def restrict_count(self, chars, password):
        """Expand the range to include count of character found in the password"""
        count = sum((c in chars) for c in password)
        self.restrict(count)

    def restrict_duplicated(self, chars, password):
        """
        Expand the range to include the number of duplicated characters
        found in the password
        """
        for c in chars:
            self.restrict(password.count(c))

    def is_valid(self):
        return self.min <= self.max

    def get_range(self):
        self._raise_if_not_valid()
        return range(self.min, self.max + 1)

    def ensure_range(self, value):
        self._raise_if_not_valid()
        value = max(value, self.min)
        value = min(value, self.max)
        return value

    def _raise_if_not_valid(self):
        if not self.is_valid():
            raise Exception('The operation cannot be used on an invalid rule.')

    def __str__(self):
        if self.is_valid():
            return '[{0}..{1}]'.format(self.min, self.max)
        return '[Invalid rule!]'


class CharSetRule:
    """
    Represents the rule for a set of characters and contains
    the minimum and maximum numbers of characters together with the
    mininum and maximum number of duplicates allowed using the char set.
    """
    def __init__(self, name, chars):
        self.name = name
        self.chars = chars
        self.count = RangeRule()
        self.duplication = RangeRule()

    def learn(self, password):
        self.count.restrict_count(self.chars, password)
        self.duplication.restrict_duplicated(self.chars, password)
        
    def is_valid(self):
        if not (self.count.is_valid() and self.duplication.is_valid()):
            return False
        if self.count.min == self.count.max and self.count.min == 0:
            return False
        if self.duplication.min != 0 or self.duplication.max == 0:
            return False
        return True

    def __str__(self):
        return '{0: <8} count in {1}, duplication in {2}'.format(self.name, self.count, self.duplication)


class PasswordRules:
    """
    Represents all the rules for the allowed passwords.
    This rules are used to generate passwords that match the given rules.
    """

    def __init__(self):
        self.length = RangeRule()
        self._charset_rules = []
        self.groups = {
            'digit': '1234567890',
            'special': '!"#$%&\'()*+,-./:;?@[\\]^_`{|}~',
            'lower': 'abcdefghijklmnopqrstuvwxyz',
            'upper': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        }
        for key in self.groups:
            val = self.groups[key]
            self._charset_rules.append(CharSetRule(key, val))
    
    def learn(self, password):
        """Learn the rules of the password by feeding examples."""
        self.length.restrict(len(password))

        for rule in self._charset_rules:
            rule.learn(password)

    def get_charsets(self):
        result = []
        for rule in self._charset_rules:
            if rule.is_valid():
                result.append(rule)
        return result

    def __str__(self):
        """String representation of the rules that apply for generating passwords."""
        lines = [ 'password length in {0}'.format(self.length) ]
        for rule in self.get_charsets():
            lines.append('{0}'.format(rule))
        return '\n'.join(lines)
