#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "fastaccess/entry.hpp"
#include "fastaccess/index.hpp"
#include "fastaccess/store.hpp"
#include "fastaccess/complement.hpp"

namespace py = pybind11;

PYBIND11_MODULE(_fastaccess_cpp, m) {
    m.doc() = "C++ backend for fastaccess FASTA random access library";

    // Expose Entry struct
    py::class_<fastaccess::Entry>(m, "Entry")
        .def(py::init<>())
        .def(py::init<std::string, std::string, int64_t, int32_t, int32_t, int64_t>(),
             py::arg("name"),
             py::arg("description"),
             py::arg("length"),
             py::arg("line_blen"),
             py::arg("line_len"),
             py::arg("offset"))
        .def_readwrite("name", &fastaccess::Entry::name)
        .def_readwrite("description", &fastaccess::Entry::description)
        .def_readwrite("length", &fastaccess::Entry::length)
        .def_readwrite("line_blen", &fastaccess::Entry::line_blen)
        .def_readwrite("line_len", &fastaccess::Entry::line_len)
        .def_readwrite("offset", &fastaccess::Entry::offset)
        .def("__repr__", [](const fastaccess::Entry& e) {
            return "Entry(name='" + e.name + "', length=" + std::to_string(e.length) + ")";
        });

    // Expose build_index function
    m.def("build_index", &fastaccess::build_index,
          py::arg("path"),
          R"pbdoc(
              Build an in-memory index of all FASTA records in the file.

              Args:
                  path: Path to the FASTA file

              Returns:
                  Dictionary mapping sequence name to Entry with index information
          )pbdoc");

    // Expose fetch_subseq function
    m.def("fetch_subseq", &fastaccess::fetch_subseq,
          py::arg("path"),
          py::arg("index"),
          py::arg("name"),
          py::arg("start"),
          py::arg("stop"),
          R"pbdoc(
              Fetch a subsequence using 1-based inclusive coordinates.

              Args:
                  path: Path to the FASTA file
                  index: Pre-built index dictionary
                  name: Sequence name
                  start: Start position (1-based, inclusive)
                  stop: Stop position (1-based, inclusive)

              Returns:
                  Uppercase string containing the requested subsequence
          )pbdoc");

    // Expose fetch_many function
    m.def("fetch_many", &fastaccess::fetch_many,
          py::arg("path"),
          py::arg("index"),
          py::arg("queries"),
          R"pbdoc(
              Fetch multiple subsequences in batch.

              Args:
                  path: Path to the FASTA file
                  index: Pre-built index dictionary
                  queries: List of (name, start, stop) tuples

              Returns:
                  List of uppercase strings, one for each query
          )pbdoc");

    // Expose reverse_complement function
    m.def("reverse_complement", &fastaccess::reverse_complement,
          py::arg("seq"),
          R"pbdoc(
              Get the reverse complement of a DNA sequence.

              Args:
                  seq: Input sequence (uppercase)

              Returns:
                  Reverse complement of the sequence
          )pbdoc");

    // Version info
    m.attr("__version__") = "0.2.0";
}
