#include "fastaccess/complement.hpp"
#include <algorithm>

namespace fastaccess {

// Compile-time lookup table for DNA complement
// Handles IUPAC ambiguity codes
// Use unsigned char to avoid narrowing issues on signed char platforms
static constexpr unsigned char COMPLEMENT_TABLE[256] = {
    // 0-31: control characters (unchanged)
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31,
    // 32-47: space and punctuation (unchanged)
    ' ', '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/',
    // 48-63: digits and more punctuation (unchanged)
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
    // 64-79: @ and uppercase A-O
    '@',
    'T',  // A -> T
    'V',  // B -> V (B = C/G/T, V = A/C/G)
    'G',  // C -> G
    'H',  // D -> H (D = A/G/T, H = A/C/T)
    'E',  // E (unchanged, not standard)
    'F',  // F (unchanged, not standard)
    'C',  // G -> C
    'D',  // H -> D
    'I',  // I (unchanged, not standard)
    'J',  // J (unchanged, not standard)
    'M',  // K -> M (K = G/T, M = A/C)
    'L',  // L (unchanged, not standard)
    'K',  // M -> K
    'N',  // N -> N (any base)
    'O',  // O (unchanged, not standard)
    // 80-95: P-Z and more
    'P',  // P (unchanged, not standard)
    'Q',  // Q (unchanged, not standard)
    'Y',  // R -> Y (R = A/G, Y = C/T)
    'S',  // S -> S (S = C/G, self-complement)
    'A',  // T -> A
    'U',  // U (unchanged - RNA)
    'B',  // V -> B
    'W',  // W -> W (W = A/T, self-complement)
    'X',  // X (unchanged, not standard)
    'R',  // Y -> R
    'Z',  // Z (unchanged, not standard)
    '[', '\\', ']', '^', '_',
    // 96-111: backtick and lowercase a-o
    '`',
    't',  // a -> t
    'v',  // b -> v
    'g',  // c -> g
    'h',  // d -> h
    'e',  // e
    'f',  // f
    'c',  // g -> c
    'd',  // h -> d
    'i',  // i
    'j',  // j
    'm',  // k -> m
    'l',  // l
    'k',  // m -> k
    'n',  // n -> n
    'o',  // o
    // 112-127: p-z and more
    'p',  // p
    'q',  // q
    'y',  // r -> y
    's',  // s -> s
    'a',  // t -> a
    'u',  // u
    'b',  // v -> b
    'w',  // w -> w
    'x',  // x
    'r',  // y -> r
    'z',  // z
    '{', '|', '}', '~', 127,
    // 128-255: extended ASCII (unchanged)
    128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143,
    144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159,
    160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175,
    176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191,
    192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207,
    208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223,
    224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239,
    240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255
};

std::string reverse_complement(const std::string& seq) {
    std::string result;
    result.reserve(seq.size());

    // Iterate in reverse and complement each base
    for (auto it = seq.rbegin(); it != seq.rend(); ++it) {
        result.push_back(static_cast<char>(COMPLEMENT_TABLE[static_cast<unsigned char>(*it)]));
    }

    return result;
}

void reverse_complement_inplace(std::string& seq) {
    if (seq.empty()) return;

    size_t left = 0;
    size_t right = seq.size() - 1;

    while (left < right) {
        // Swap and complement
        unsigned char temp = COMPLEMENT_TABLE[static_cast<unsigned char>(seq[left])];
        seq[left] = static_cast<char>(COMPLEMENT_TABLE[static_cast<unsigned char>(seq[right])]);
        seq[right] = static_cast<char>(temp);
        ++left;
        --right;
    }

    // Handle middle element if odd length
    if (left == right) {
        seq[left] = static_cast<char>(COMPLEMENT_TABLE[static_cast<unsigned char>(seq[left])]);
    }
}

} // namespace fastaccess
