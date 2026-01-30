#pragma once

#include <string>
#include <unordered_map>
#include "entry.hpp"

namespace fastaccess {

// Type alias for the index
using Index = std::unordered_map<std::string, Entry>;

/**
 * Build an in-memory index of all FASTA records in the file.
 *
 * Single pass over FASTA:
 *   - Parse headers (>name ...)
 *   - Detect newline style (\n or \r\n)
 *   - Detect first sequence line width (line_blen) and full line bytes (line_len)
 *   - Accumulate total base length (strip newline bytes)
 *   - Record byte offset where sequence starts
 *
 * @param path Path to the FASTA file
 * @return Dictionary mapping sequence name to Entry with index information
 * @throws std::runtime_error if file cannot be opened
 */
Index build_index(const std::string& path);

} // namespace fastaccess
