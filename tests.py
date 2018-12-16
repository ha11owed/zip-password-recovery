#!/usr/bin/env python

import unittest

from rules import PasswordRules
from generator import PasswordGenerator, PasswordVerifier
from zippass import ZipPassCracker
from mathhelpers import combinations, factorial, permutations

class RulesTests(unittest.TestCase):

    def test_unitialized(self):
        rules = PasswordRules()
        self.assertFalse(rules.length.is_valid())
        self.assertEqual(0, len(rules.get_charsets()))

    def test_digits_and_lower_only(self):
        rules = PasswordRules()
        rules.learn('abc1')
        rules.learn('abb12')
        self.assertEqual(4, rules.length.min)
        self.assertEqual(5, rules.length.max)
        charsets = rules.get_charsets()
        self.assertEqual(2, len(charsets))
        self.assertEqual('digit', charsets[0].name)
        self.assertEqual(1, charsets[0].count.min)
        self.assertEqual(2, charsets[0].count.max)
        self.assertEqual(0, charsets[0].duplication.min)
        self.assertEqual(1, charsets[0].duplication.max)
        self.assertEqual('lower', charsets[1].name)
        self.assertEqual(3, charsets[1].count.min)
        self.assertEqual(3, charsets[1].count.max)
        self.assertEqual(0, charsets[1].duplication.min)
        self.assertEqual(2, charsets[1].duplication.max)

    def test_digits_and_lower_fixed_length(self):
        rules = PasswordRules()
        rules.learn('abcd1')
        rules.learn('abb12')
        self.assertEqual(5, rules.length.min)
        self.assertEqual(5, rules.length.max)
        charsets = rules.get_charsets()
        self.assertEqual(2, len(charsets))
        self.assertEqual('digit', charsets[0].name)
        self.assertEqual(1, charsets[0].count.min)
        self.assertEqual(2, charsets[0].count.max)
        self.assertEqual(0, charsets[0].duplication.min)
        self.assertEqual(1, charsets[0].duplication.max)
        self.assertEqual('lower', charsets[1].name)
        self.assertEqual(3, charsets[1].count.min)
        self.assertEqual(4, charsets[1].count.max)
        self.assertEqual(0, charsets[1].duplication.min)
        self.assertEqual(2, charsets[1].duplication.max)


class GeneratorTests(unittest.TestCase):
    
    def test_empty(self):
        rules = PasswordRules()
        generator = PasswordGenerator(rules)
        snapshots = [ s for s in generator.iter_rules() ]
        self.assertEqual(0, len(snapshots))
        self.assertEqual(0, generator.count_rules())

    def test_digits_and_lower_single_password(self):
        rules = PasswordRules()
        rules.learn('ab1')
        generator = PasswordGenerator(rules)
        self.assertEqual(1, generator.count_rules())
        snapshots = [ s for s in generator.iter_rules() ]
        self.assertEqual(1, len(snapshots))
        self.assertEqual([1, 2], snapshots[0].counts)
        passwords = [ p for p in snapshots[0].iter_passwords() ]
        expected = (permutations(10, 1) * permutations(26, 2)) * 3
        self.assertEqual(expected, len(passwords))

    def test_digits_and_lower_passwords_short(self):
        rules = PasswordRules()
        rules.learn('a1')
        rules.learn('ab1')
        generator = PasswordGenerator(rules)
        snapshots = [ s for s in generator.iter_rules() ]
        self.assertEqual(2, len(snapshots))
        # 1|a
        self.assertEqual([1, 1], snapshots[0].counts)
        self.assertEqual(26 * 10 * 2, snapshots[0].count_passwords())
        # 1|ab
        self.assertEqual([1, 2], snapshots[1].counts)
        self.assertEqual((26 * 25 / 2) * 10 * 3, snapshots[1].count_passwords())

    def test_digits_and_lower_passwords_fixed_lenght(self):
        rules = PasswordRules()
        rules.learn('abcde1')
        rules.learn('aacd12')
        generator = PasswordGenerator(rules)
        snapshots = [ s for s in generator.iter_rules() ]
        self.assertEqual(2, len(snapshots))
        self.assertEqual([2, 4], snapshots[0].counts)
        self.assertEqual([1, 5], snapshots[1].counts)

    def test_password_count(self):
        rules = PasswordRules()
        rules.learn('abbdABBD12')
        rules.learn('abbdABBD^2')
        generator = PasswordGenerator(rules)
        self.assertEqual(2, generator.count_rules())
        snapshots = [ s for s in generator.iter_rules() ]
        self.assertEqual(2, len(snapshots))
        self.assertEqual([4, 2, 4, 0], snapshots[0].counts)
        chs = (26*2)*(26*2-1)*(26*2-2)*(26*2-3)/(2*3*4)
        self.assertEqual(10 * chs * chs * (10 * 9 / 2), snapshots[0].count_passwords())
        self.assertEqual([4, 1, 4, 1], snapshots[1].counts)
        self.assertEqual(10 * chs * chs * 10 * 29, snapshots[1].count_passwords())


class PasswordVerifierTests(unittest.TestCase):

    def test_secret_zip(self):
        cracker = PasswordVerifier(lambda p : p == 'p@s1', [ 'ab_1' ])
        self.assertTrue(cracker.is_password('p@s1'))
        password = cracker.try_passwords()
        self.assertEqual('p@s1', password)


if __name__ == '__main__':
    unittest.main()
