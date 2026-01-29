#! /usr/bin/python3

r'''###############################################################################
###################################################################################
#
#
#	midiharmony Python module
#	Version 1.0
#
#	Project Los Angeles
#
#	Tegridy Code 2026
#
#   https://github.com/Tegridy-Code/Project-Los-Angeles
#
#
###################################################################################
###################################################################################
#
#   Copyright 2026 Project Los Angeles / Tegridy Code
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
###################################################################################
###################################################################################
#
#   Critical dependencies
#
#   !pip install cupy-cuda12x
#   !pip install matplotlib
#   !pip install numpy==1.26.4
#   !pip install tqdm
#
###################################################################################
'''

###################################################################################
###################################################################################

print('=' * 70)
print('Loading midiharmony Python module...')
print('Please wait...')
print('=' * 70)

__version__ = '1.0.0'

print('midiharmony module version', __version__)
print('=' * 70)

###################################################################################
###################################################################################

import os

from typing import List, Optional, Union, Tuple, Dict, Any

import tqdm

try:
    import cupy as cp
    
except:
    print('Could not load CuPy!')

import numpy as np

from . import TMIDIX

###################################################################################

def midiharmony():
    """main function placeholder"""
    return None

###################################################################################

print('Module is loaded!')
print('Enjoy! :)')
print('=' * 70)

###################################################################################
# This is the end of the midiharmony Python module
###################################################################################