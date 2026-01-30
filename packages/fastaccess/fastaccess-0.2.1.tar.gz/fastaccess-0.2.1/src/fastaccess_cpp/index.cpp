#include "fastaccess/index.hpp"
#include "fastaccess/gzip_utils.hpp"
#include <fstream>
#include <stdexcept>
#include <cstring>
#include <vector>

namespace fastaccess {

namespace {

// Parse header line to extract name and description
inline std::pair<std::string, std::string> parse_header(const char* data, size_t len) {
    // Skip the '>' character
    if (len > 0 && data[0] == '>') {
        ++data;
        --len;
    }

    // Strip trailing whitespace
    while (len > 0 && (data[len - 1] == '\r' || data[len - 1] == '\n' ||
                       data[len - 1] == ' ' || data[len - 1] == '\t')) {
        --len;
    }

    // Find first whitespace to split name from description
    size_t name_end = 0;
    while (name_end < len && data[name_end] != ' ' && data[name_end] != '\t') {
        ++name_end;
    }

    std::string name(data, name_end);
    std::string description;

    // Skip whitespace between name and description
    size_t desc_start = name_end;
    while (desc_start < len && (data[desc_start] == ' ' || data[desc_start] == '\t')) {
        ++desc_start;
    }

    if (desc_start < len) {
        description = std::string(data + desc_start, len - desc_start);
    }

    return {name, description};
}

} // anonymous namespace

Index build_index(const std::string& path) {
    // Read file into memory (handles gzip transparently)
    std::vector<char> buffer = read_file_to_memory(path);

    Index index;
    const char* data = buffer.data();
    const char* end = data + buffer.size();

    std::string current_name;
    std::string current_description;
    int64_t current_offset = 0;
    int64_t current_length = 0;
    int32_t current_line_blen = 0;
    int32_t current_line_len = 0;
    bool first_seq_line = true;
    bool in_sequence = false;

    while (data < end) {
        // Find end of line
        const char* line_start = data;
        const char* line_end = data;
        while (line_end < end && *line_end != '\n') {
            ++line_end;
        }

        // Calculate line length including newline
        size_t line_len_with_nl = (line_end < end) ? (line_end - line_start + 1) : (line_end - line_start);

        // Get content length (excluding newlines)
        size_t content_len = line_end - line_start;
        // Strip \r if present (Windows line endings)
        if (content_len > 0 && line_start[content_len - 1] == '\r') {
            --content_len;
        }

        if (content_len > 0 && line_start[0] == '>') {
            // Header line - save previous entry if exists
            if (in_sequence && !current_name.empty()) {
                index[current_name] = Entry(
                    current_name,
                    current_description,
                    current_length,
                    current_line_blen,
                    current_line_len,
                    current_offset
                );
            }

            // Parse header
            auto [name, desc] = parse_header(line_start, content_len);
            current_name = name;
            current_description = desc;

            // Offset is position after this line
            current_offset = (line_end < end) ? (line_end - buffer.data() + 1) : (line_end - buffer.data());
            current_length = 0;
            current_line_blen = 0;
            current_line_len = 0;
            first_seq_line = true;
            in_sequence = true;
        } else if (in_sequence && content_len > 0) {
            // Sequence line
            if (first_seq_line) {
                // Check if there's another sequence line after this
                const char* next_line = (line_end < end) ? (line_end + 1) : end;
                bool has_more_sequence = (next_line < end && *next_line != '>');

                if (has_more_sequence) {
                    // Wrapped sequence
                    current_line_blen = static_cast<int32_t>(content_len);
                    current_line_len = static_cast<int32_t>(line_len_with_nl);
                } else {
                    // Unwrapped (single line)
                    current_line_blen = 0;
                    current_line_len = 0;
                }

                first_seq_line = false;
            }

            current_length += content_len;
        }

        // Move to next line
        data = (line_end < end) ? (line_end + 1) : end;
    }

    // Save last entry
    if (in_sequence && !current_name.empty()) {
        index[current_name] = Entry(
            current_name,
            current_description,
            current_length,
            current_line_blen,
            current_line_len,
            current_offset
        );
    }

    return index;
}

} // namespace fastaccess
