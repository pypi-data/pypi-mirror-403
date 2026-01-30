# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Station Constants"""

from .constants import N_pol

# pylint: disable=consider-using-f-string, invalid-name

# maximum number of fpgas supported by SDP
N_pn = 16

# antennas per FPGA
A_pn = 6

# signal inputs per FPGA
S_pn = A_pn * N_pol

# Number of tile elements (antenna dipoles) in each HBA tile
N_elements = 16

# number of RCU's per subrack
N_rcu = 32

# Number of antenna inputs per RCU
N_rcu_inp = 3

# number of uniboards in a subrack
N_unb = 2

# number of FPGA's in a uniboard
N_fpga = 4

# number of actively controlled beamlets
N_beamlets_ctrl = 488

# Maximum number of subbands we support
N_subbands = 512
