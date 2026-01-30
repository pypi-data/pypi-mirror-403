cmake_minimum_required(VERSION 3.15)
project(fastaccess LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find pybind11
find_package(pybind11 CONFIG REQUIRED)

# Find zlib for gzip support
find_package(ZLIB REQUIRED)

# Add subdirectory with C++ sources
add_subdirectory(src/fastaccess_cpp)
