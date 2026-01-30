# Source files
set(SOURCES
    entry.cpp
    index.cpp
    store.cpp
    complement.cpp
    gzip_utils.cpp
    bindings.cpp
)

# Create pybind11 module
pybind11_add_module(_fastaccess_cpp ${SOURCES})

# Include directories
target_include_directories(_fastaccess_cpp PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link zlib for gzip support
target_link_libraries(_fastaccess_cpp PRIVATE ZLIB::ZLIB)

# Compiler optimizations for Release builds
target_compile_options(_fastaccess_cpp PRIVATE
    $<$<CONFIG:Release>:-O3>
    $<$<CONFIG:Release>:-DNDEBUG>
)

# Install to fastaccess package directory
install(TARGETS _fastaccess_cpp LIBRARY DESTINATION fastaccess)
