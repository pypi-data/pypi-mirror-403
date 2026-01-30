#include "fastaccess/gzip_utils.hpp"
#include <fstream>
#include <stdexcept>
#include <zlib.h>

namespace fastaccess {

bool is_gzipped(const std::string& path) {
    return path.size() >= 3 && path.substr(path.size() - 3) == ".gz";
}

std::vector<char> decompress_gzip(const std::string& path) {
    gzFile gz = gzopen(path.c_str(), "rb");
    if (!gz) {
        throw std::runtime_error("Cannot open gzip file: " + path);
    }

    std::vector<char> result;
    const size_t chunk_size = 1024 * 1024;  // 1 MB chunks
    std::vector<char> buffer(chunk_size);

    int bytes_read;
    while ((bytes_read = gzread(gz, buffer.data(), static_cast<unsigned>(chunk_size))) > 0) {
        result.insert(result.end(), buffer.begin(), buffer.begin() + bytes_read);
    }

    if (bytes_read < 0) {
        int err;
        const char* error_msg = gzerror(gz, &err);
        gzclose(gz);
        throw std::runtime_error("Error decompressing gzip file: " + std::string(error_msg));
    }

    gzclose(gz);
    return result;
}

std::vector<char> read_file_to_memory(const std::string& path) {
    if (is_gzipped(path)) {
        return decompress_gzip(path);
    }

    // Regular file - read directly
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file) {
        throw std::runtime_error("Cannot open file: " + path);
    }

    auto file_size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::vector<char> buffer(static_cast<size_t>(file_size));
    file.read(buffer.data(), file_size);

    return buffer;
}

} // namespace fastaccess
