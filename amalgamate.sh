#!/bin/bash

python amalgamate.py rules.py generator.py zippass.py main.py

rm zippy.py
mv __amalgam__.py zippy.py
chmod a+x zippy.py
