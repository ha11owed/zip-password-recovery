#!/usr/bin/env python
"""Generated file. Amalgated from: rules.py, generator.py, zippass.py, main.py"""

import sys
import time
import zipfile
import itertools
from mathhelpers import combinations, factorial, permutations
import io

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



class RuleIterator:
    def __init__(self, rule, count=None):
        if count is None:
            count = rule.count.min
        self.rule = rule
        self.count = count

    def count_range(self):
        return range(self.rule.count.min, self.rule.count.max + 1)

    def count_combinations(self):
        max_dup = min(self.rule.duplication.max, self.count)
        n = max_dup * len(self.rule.chars)
        k = self.count
        return combinations(n, k)

    def iter_combinations(self):
        chars = ''
        max_dup = min(self.rule.duplication.max, self.count)
        for i in range(0, max_dup):
            chars += self.rule.chars
        for combination in itertools.combinations(chars, self.count):
            combination_str = ''.join(combination)
            #print('combination: {0}'.format(combination_str))
            yield combination_str

    def __str__(self):
        return '{0: <8} count={1}. duplication={2}'.format(self.rule.name, self.count, self.rule.duplication.max)


class RulesSnapshot:
    def __init__(self, rule_iterators):
        self.counts = []
        self._rules = []
        for rule_it in rule_iterators:
            self.counts.append(rule_it.count)
            self._rules.append(rule_it.rule)

    def count_passwords(self):
        rule_iterators = self._rule_iterators()
        n = sum(rit.count for rit in rule_iterators)
        for i, rit in enumerate(rule_iterators):
            k = rit.count_combinations()
            n *= k
            #print('n={0}, k={1}. count={2}, self={3}'.format(n, k, rit.count, self))
        return n

    def iter_passwords(self):
        for composition in self._iter_composition():
            for password in itertools.permutations(composition):
                yield ''.join(password)

    def _iter_composition(self):
        rule_iterators = self._rule_iterators()
        n = len(rule_iterators)
        iterators = [ rit.iter_combinations() for rit in rule_iterators ]
        compositions = []
        for rit in iterators:
            compositions.append(next(rit))
        yield ''.join(compositions)
        for composition in self._iter_composition_recursive(iterators, compositions, 0):
            yield composition

    def _iter_composition_recursive(self, iterators, compositions, index):
        if index >= len(iterators):
            return
        while True:
            try:
                for composition in self._iter_composition_recursive(iterators, compositions, index + 1):
                    yield composition
                compositions[index] = next(iterators[index])
                yield ''.join(compositions)
            except StopIteration:
                iterators[index] = self._rule_iterator(index).iter_combinations()
                compositions[index] = next(iterators[index])
                break

    def _rule_iterator(self, index):
        return RuleIterator(self._rules[index], self.counts[index])

    def _rule_iterators(self):
        return [ RuleIterator(r, self.counts[i]) for i, r in enumerate(self._rules) ]

    def equals(self, other):
        if self is other:
            return True
        if other is None:
            return False
        n = len(self.counts)
        if n != len(other.counts):
            return False
        for i in range(0, n):
            if self.counts[i] != other.counts[i]:
                return False
        return True

    def __str__(self):
        return '|'.join(str(c) for c in self.counts)

    def __eq__(self, other):
        return self.equals(other)

    def __ne__(self, other):
        return not self.equals(other)

    def __hash__(self):
        h = len(self.counts)
        for i, v in enumerate(self.counts):
            h += 17 * (i + 1) * (v + 10)
        return h


class PasswordGenerator:
    """Iterate over all the possible passwords using the specified password rules."""

    def __init__(self, password_rules):
        self.password_rules = password_rules

    def count_rules(self):
        # This could be optimized for speed to use a mathematical formula
        return sum(1 for _ in self.iter_rules())

    def iter_rules(self):
        snapshots = set()
        pr = self.password_rules
        for length in range(pr.length.min, pr.length.max + 1):
            rule_iterators = []
            for rule in pr.get_charsets():
                rule_iterators.append(RuleIterator(rule))
            self._iter_rules_recursive(rule_iterators, length, 0, snapshots)
        return snapshots

    def _iter_rules_recursive(self, rule_iterators, length, index, snapshots):
        if index >= len(rule_iterators):
            return
        rule_it = rule_iterators[index]
        for cnt in rule_it.count_range():
            rule_it.count = cnt
            if self._validate(rule_iterators, length):
                snapshot = RulesSnapshot(rule_iterators)
                snapshots.add(snapshot)
            self._iter_rules_recursive(rule_iterators, length, index + 1, snapshots)

    def _validate(self, rule_iterators, length):
        s = sum(rit.count for rit in rule_iterators)
        return s == length

    def __str__(self):
        return 'PasswordGenerator for {0}'.format(self.password_rules)


class PasswordVerifier:

    def __init__(self, password_examples, is_password):
        rules = PasswordRules()
        for example in password_examples:
            rules.learn(example)
        self.generator = PasswordGenerator(rules)
        self.is_password = is_password

    def try_passwords(self):
        gen = self.generator
        for rit in gen.iter_rules():
            print('Rule iterator: {0}'.format(rit))
            begin = time.time()
            for password in rit.iter_passwords():
                if self.is_password(password):
                    return password
            end = time.time()
            seconds = end - begin
            print('Done in {0} seconds'.format(seconds))
        return None

    def __str__(self):
        return 'ZipPassCracker File: {0}\n{1}'.format(self.filepath, self.generator)



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

if __name__ == '__main__':
    examples = [ 'aa1&', 'Abaer1&' ]
    cracker = ZipPassCracker('secret.zip', examples)
    password = cracker.try_passwords()
    print('Password: "{0}"'.format(password))
