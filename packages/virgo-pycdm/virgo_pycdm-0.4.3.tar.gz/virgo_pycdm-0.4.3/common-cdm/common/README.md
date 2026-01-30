Code shared between the BSDA, EBIs and client programs.

Avoid using plain C-style arrays as it would break pybind constructs (use std::array instead, which looks identical to C-style array in most implementations and we check this is the case in bsda firmware in a compile-time test).
