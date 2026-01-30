#include "fastaccess/store.hpp"
#include "fastaccess/gzip_utils.hpp"
#include <fstream>
#include <stdexcept>
#include <algorithm>
#include <cctype>
#include <cstring>

namespace fastaccess {

namespace {

// Helper to fetch from a memory buffer (used for gzip files)
std::string fetch_from_buffer(const char* data, size_t data_size,
                              const Entry& entry, int64_t start, int64_t stop) {
    int64_t num_bases = stop - start + 1;
    std::string result;
    result.reserve(static_cast<size_t>(num_bases));

    if (entry.line_blen == 0) {
        // Unwrapped sequence - simple offset and read
        int64_t byte_pos = entry.offset + (start - 1);
        if (byte_pos + num_bases > static_cast<int64_t>(data_size)) {
            throw std::runtime_error("Read position exceeds file size");
        }

        result.resize(static_cast<size_t>(num_bases));
        std::memcpy(&result[0], data + byte_pos, static_cast<size_t>(num_bases));

        // Convert to uppercase in-place
        for (char& c : result) {
            c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        }
    } else {
        // Wrapped sequence - calculate bytes to read including newlines
        int64_t zero_based_start = start - 1;
        int64_t zero_based_stop = stop - 1;

        // Which line (0-indexed) does our start position fall on?
        int64_t start_line = zero_based_start / entry.line_blen;
        int64_t start_within_line = zero_based_start % entry.line_blen;

        // Which line does our stop position fall on?
        int64_t stop_line = zero_based_stop / entry.line_blen;
        int64_t stop_within_line = zero_based_stop % entry.line_blen;

        // Calculate byte positions
        int64_t start_byte = entry.offset + start_line * entry.line_len + start_within_line;
        int64_t stop_byte = entry.offset + stop_line * entry.line_len + stop_within_line;

        // Read all bytes at once (including newlines)
        int64_t bytes_to_read = stop_byte - start_byte + 1;

        if (start_byte + bytes_to_read > static_cast<int64_t>(data_size)) {
            throw std::runtime_error("Read position exceeds file size");
        }

        // Filter out newlines and convert to uppercase
        result.reserve(static_cast<size_t>(num_bases));
        for (int64_t i = 0; i < bytes_to_read; ++i) {
            char c = data[start_byte + i];
            if (c != '\n' && c != '\r') {
                result.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));
            }
        }
    }

    return result;
}

// Helper to fetch from a file stream (used for regular files)
std::string fetch_from_file(std::ifstream& file, const Entry& entry,
                            int64_t start, int64_t stop) {
    int64_t num_bases = stop - start + 1;
    std::string result;
    result.reserve(static_cast<size_t>(num_bases));

    if (entry.line_blen == 0) {
        // Unwrapped sequence - simple seek and read
        int64_t byte_pos = entry.offset + (start - 1);
        file.seekg(byte_pos);

        result.resize(static_cast<size_t>(num_bases));
        file.read(&result[0], num_bases);

        // Convert to uppercase in-place
        for (char& c : result) {
            c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        }
    } else {
        // Wrapped sequence - calculate bytes to read including newlines
        int64_t zero_based_start = start - 1;
        int64_t zero_based_stop = stop - 1;

        // Which line (0-indexed) does our start position fall on?
        int64_t start_line = zero_based_start / entry.line_blen;
        int64_t start_within_line = zero_based_start % entry.line_blen;

        // Which line does our stop position fall on?
        int64_t stop_line = zero_based_stop / entry.line_blen;
        int64_t stop_within_line = zero_based_stop % entry.line_blen;

        // Calculate byte positions
        int64_t start_byte = entry.offset + start_line * entry.line_len + start_within_line;
        int64_t stop_byte = entry.offset + stop_line * entry.line_len + stop_within_line;

        // Read all bytes at once (including newlines)
        int64_t bytes_to_read = stop_byte - start_byte + 1;
        std::string buffer(static_cast<size_t>(bytes_to_read), '\0');

        file.seekg(start_byte);
        file.read(&buffer[0], bytes_to_read);

        // Filter out newlines and convert to uppercase
        result.reserve(static_cast<size_t>(num_bases));
        for (char c : buffer) {
            if (c != '\n' && c != '\r') {
                result.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));
            }
        }
    }

    return result;
}

} // anonymous namespace

std::string fetch_subseq(const std::string& path, const Index& index,
                         const std::string& name, int64_t start, int64_t stop) {
    // Validate sequence name exists
    auto it = index.find(name);
    if (it == index.end()) {
        throw std::out_of_range("Sequence '" + name + "' not found in index");
    }

    const Entry& entry = it->second;

    // Validate coordinates
    if (start < 1) {
        throw std::invalid_argument("Start position must be >= 1, got " + std::to_string(start));
    }
    if (stop < start) {
        throw std::invalid_argument("Stop position must be >= start, got start=" +
                                    std::to_string(start) + ", stop=" + std::to_string(stop));
    }
    if (stop > entry.length) {
        throw std::invalid_argument("Stop position " + std::to_string(stop) +
                                    " exceeds sequence length " + std::to_string(entry.length) +
                                    " for '" + name + "'");
    }

    // Handle gzip files
    if (is_gzipped(path)) {
        std::vector<char> data = read_file_to_memory(path);
        return fetch_from_buffer(data.data(), data.size(), entry, start, stop);
    }

    // Regular file
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Cannot open file: " + path);
    }

    return fetch_from_file(file, entry, start, stop);
}

std::vector<std::string> fetch_many(
    const std::string& path,
    const Index& index,
    const std::vector<std::tuple<std::string, int64_t, int64_t>>& queries) {

    std::vector<std::string> results;
    results.reserve(queries.size());

    // For gzip files, decompress once and reuse the buffer
    if (is_gzipped(path)) {
        std::vector<char> data = read_file_to_memory(path);

        for (const auto& query : queries) {
            const std::string& name = std::get<0>(query);
            int64_t start = std::get<1>(query);
            int64_t stop = std::get<2>(query);

            // Validate sequence name exists
            auto it = index.find(name);
            if (it == index.end()) {
                throw std::out_of_range("Sequence '" + name + "' not found in index");
            }

            const Entry& entry = it->second;

            // Validate coordinates
            if (start < 1) {
                throw std::invalid_argument("Start position must be >= 1, got " + std::to_string(start));
            }
            if (stop < start) {
                throw std::invalid_argument("Stop position must be >= start, got start=" +
                                            std::to_string(start) + ", stop=" + std::to_string(stop));
            }
            if (stop > entry.length) {
                throw std::invalid_argument("Stop position " + std::to_string(stop) +
                                            " exceeds sequence length " + std::to_string(entry.length) +
                                            " for '" + name + "'");
            }

            results.push_back(fetch_from_buffer(data.data(), data.size(), entry, start, stop));
        }
        return results;
    }

    // Regular file - use file-based fetch
    for (const auto& query : queries) {
        results.push_back(fetch_subseq(
            path, index,
            std::get<0>(query),
            std::get<1>(query),
            std::get<2>(query)
        ));
    }

    return results;
}

} // namespace fastaccess
