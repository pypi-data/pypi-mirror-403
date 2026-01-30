#pragma once

#include <array>

constexpr unsigned k_num_boards = 3;

template <typename T> using BB = std::array<T, k_num_boards>;
