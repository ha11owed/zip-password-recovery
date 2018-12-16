import sys
import time
import zipfile
import itertools

from rules import PasswordRules
from mathhelpers import combinations, factorial, permutations


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
