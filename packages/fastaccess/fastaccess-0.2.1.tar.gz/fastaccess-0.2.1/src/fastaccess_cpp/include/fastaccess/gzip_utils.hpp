#pragma once

#include <string>
#include <vector>

namespace fastaccess {

/**
 * Check if a file path indicates a gzip-compressed file.
 *
 * @param path File path to check
 * @return true if path ends with ".gz"
 */
bool is_gzipped(const std::string& path);

/**
 * Decompress a gzip file to memory.
 *
 * @param path Path to the gzip-compressed file
 * @return Vector containing the decompressed data
 * @throws std::runtime_error if file cannot be opened or decompression fails
 */
std::vector<char> decompress_gzip(const std::string& path);

/**
 * Read a file (compressed or not) into memory.
 *
 * @param path Path to the file (may be gzipped)
 * @return Vector containing the file data (decompressed if necessary)
 * @throws std::runtime_error if file cannot be opened
 */
std::vector<char> read_file_to_memory(const std::string& path);

} // namespace fastaccess
