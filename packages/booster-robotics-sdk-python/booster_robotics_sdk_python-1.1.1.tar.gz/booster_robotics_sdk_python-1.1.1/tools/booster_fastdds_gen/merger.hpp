#pragma once

#include <iostream>
#include <string>
#include "header_merger.hpp"
#include "cpp_merger.hpp"

struct FileInput {
    std::string h_file = "";
    std::string pub_sub_types_h_file = "";
    std::string h_output_file = "";

    std::string cxx_file = "";
    std::string pub_sub_cxx_file = "";
    std::string cpp_output_file = "";
    std::string cdr_aux_hpp_file = "";
    std::string cdr_aux_ipp_file = "";

    std::string file_name = "";
    std::string source_path = "";
    std::string output_path = "";
};

class Merger {
public:
    Merger(const FileInput &file_input) :
        file_input_(file_input) {
    }

    int Merge() {
        HeaderMerger header_merger;
        int res = header_merger.Merge(
            file_input_.h_file,
            file_input_.pub_sub_types_h_file,
            file_input_.h_output_file);
        if (res != 0) {
            std::cerr << "Error: Merging header files failed." << std::endl;
            return res;
        }

        CppMerger cpp_merger;
        cpp_merger.class_name_ = header_merger.class_name_;
        res = cpp_merger.Merge(
            file_input_.cxx_file,
            file_input_.pub_sub_cxx_file,
            file_input_.cpp_output_file,
            file_input_.cdr_aux_hpp_file,
            file_input_.cdr_aux_ipp_file);
        if (res != 0) {
            std::cerr << "Error: Merging cpp files failed." << std::endl;
            return res;
        }

        return 0;
    }

private:
    FileInput file_input_;
};