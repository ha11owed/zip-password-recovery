from zippass import ZipPassCracker

if __name__ == '__main__':
    examples = [ 'aa1&', 'Abaer1&' ]
    cracker = ZipPassCracker('secret.zip', examples)
    password = cracker.try_passwords()
    print('Password: "{0}"'.format(password))
