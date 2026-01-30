#pragma once

#include <string>
#include <cstdint>

namespace fastaccess {

/**
 * Index entry for a single FASTA record.
 *
 * Stores all metadata needed for random access to a sequence.
 */
struct Entry {
    std::string name;        // Sequence name (from header)
    std::string description; // Full description text after name
    int64_t length;          // Total number of bases in the sequence
    int32_t line_blen;       // Bases per full line; 0 if unwrapped (single line)
    int32_t line_len;        // Bytes per line including newline(s); 0 if unwrapped
    int64_t offset;          // Byte offset where sequence data starts

    Entry() : length(0), line_blen(0), line_len(0), offset(0) {}

    Entry(std::string name_, std::string description_, int64_t length_,
          int32_t line_blen_, int32_t line_len_, int64_t offset_)
        : name(std::move(name_))
        , description(std::move(description_))
        , length(length_)
        , line_blen(line_blen_)
        , line_len(line_len_)
        , offset(offset_)
    {}
};

} // namespace fastaccess
