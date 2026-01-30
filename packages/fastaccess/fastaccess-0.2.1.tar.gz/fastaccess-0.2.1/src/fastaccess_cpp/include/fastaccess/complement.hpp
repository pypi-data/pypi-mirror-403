#pragma once

#include <string>

namespace fastaccess {

/**
 * Get the reverse complement of a DNA sequence.
 *
 * Uses a compile-time lookup table for efficient base complementation.
 * Handles standard IUPAC ambiguity codes:
 *   A<->T, G<->C, R<->Y, S<->S, W<->W, K<->M, B<->V, D<->H, N<->N
 *
 * @param seq Input sequence (uppercase)
 * @return Reverse complement of the sequence
 */
std::string reverse_complement(const std::string& seq);

/**
 * Get the reverse complement in-place (modifies the input string).
 * More efficient for large sequences as it avoids allocation.
 *
 * @param seq Sequence to reverse complement in place
 */
void reverse_complement_inplace(std::string& seq);

} // namespace fastaccess
