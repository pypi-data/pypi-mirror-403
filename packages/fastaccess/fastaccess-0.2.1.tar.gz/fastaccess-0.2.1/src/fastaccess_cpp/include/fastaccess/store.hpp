#pragma once

#include <string>
#include <vector>
#include <tuple>
#include "index.hpp"

namespace fastaccess {

/**
 * Fetch a subsequence using 1-based inclusive coordinates.
 *
 * For wrapped sequences:
 *     - Calculate which line the start position is on
 *     - Calculate byte offset within that line
 *     - Read across lines, skipping newline bytes
 *
 * For unwrapped sequences:
 *     - Simple seek and read operation
 *
 * @param path Path to the FASTA file
 * @param index Pre-built index dictionary
 * @param name Sequence name
 * @param start Start position (1-based, inclusive)
 * @param stop Stop position (1-based, inclusive)
 * @return Uppercase string containing the requested subsequence
 * @throws std::out_of_range if sequence name not found
 * @throws std::invalid_argument if coordinates are invalid
 * @throws std::runtime_error if file cannot be opened
 */
std::string fetch_subseq(const std::string& path, const Index& index,
                         const std::string& name, int64_t start, int64_t stop);

/**
 * Fetch multiple subsequences in batch.
 *
 * @param path Path to the FASTA file
 * @param index Pre-built index dictionary
 * @param queries List of (name, start, stop) tuples
 * @return List of uppercase strings, one for each query
 */
std::vector<std::string> fetch_many(
    const std::string& path,
    const Index& index,
    const std::vector<std::tuple<std::string, int64_t, int64_t>>& queries);

} // namespace fastaccess
