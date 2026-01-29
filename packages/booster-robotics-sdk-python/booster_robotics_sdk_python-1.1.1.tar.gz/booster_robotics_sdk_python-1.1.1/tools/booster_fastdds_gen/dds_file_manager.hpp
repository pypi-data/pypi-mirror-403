#pragma once

#include <iostream>
#include <string>
#include <filesystem>
#include <unistd.h> // for getcwd
#include <limits.h> // for PATH_MAX
#include <cstdlib>

#include "merger.hpp"

namespace fs = std::filesystem;

class DdsFileManager {
public:
    std::string input_path_ = "";
    std::string source_path_ = "";
    std::string output_path_ = "";
    std::string file_name_ = "";

    DdsFileManager() = default;
    ~DdsFileManager() = default;

    int Init(const std::string &path) {
        input_path_ = path;

        char cwd[PATH_MAX];
        if (!getcwd(cwd, sizeof(cwd))) {
            std::cerr << "Error: getcwd() failed." << std::endl;
            return -1;
        }
        output_path_ = std::string(cwd);

        if (fs::path(path).is_absolute()) {
            std::cout << "Generate files from absolute path: " << path << std::endl;
            // 提取文件名
            source_path_ = path.substr(0, path.find_last_of("/"));
            int start_pos = path.find_last_of("/");
            int end_pos = path.find_last_of(".idl");
            if (start_pos == std::string::npos || end_pos == std::string::npos) {
                std::cerr << "Error: Invalid file path." << std::endl;
                return -1;
            }
            end_pos = end_pos - 4;
            int name_len = end_pos - start_pos;
            file_name_ = path.substr(start_pos + 1, name_len);
        } else {
            std::cout << "Generate files with idl file name: " << path << std::endl;

            source_path_ = std::string(cwd);
            int end_pos = path.find_last_of(".idl");
            if (end_pos == std::string::npos) {
                std::cerr << "Error: Invalid file path." << std::endl;
                return -1;
            }
            int name_len = end_pos - 3;
            file_name_ = path.substr(0, name_len);
        }
        std::cout << "Source path: " << source_path_ << std::endl;
        std::cout << "File name: " << file_name_ << std::endl;
        return 0;
    }

    void CleanupPreviousGeneratedFiles() {
        fs::remove(output_path_ + "/" + file_name_ + ".h");
        fs::remove(output_path_ + "/" + file_name_ + ".cpp");
    }

    int GenerateDdsFiles() {
        std::string command = "fastddsgen " + input_path_;
        return system(command.c_str());
    }

    std::vector<FileInput> ReadDdsGenFiles() {
        // 查找 absolute path 下的以下文件
        // - <file_name>.hpp
        // - <file_name>PubSubTypes.h
        // - <file_name>.cpp
        // - <file_name>PubSubTypes.cpp
        // - <file_name>CdrAux.hpp
        // - <file_name>CdrAux.ipp
        FileInput file_input;
        file_input.source_path = source_path_;
        file_input.output_path = output_path_;
        file_input.file_name = file_name_;
        file_input.h_file = output_path_ + "/" + file_name_ + ".h";
        file_input.pub_sub_types_h_file = output_path_ + "/" + file_name_ + "PubSubTypes.h";
        file_input.cxx_file = output_path_ + "/" + file_name_ + ".cxx";
        file_input.pub_sub_cxx_file = output_path_ + "/" + file_name_ + "PubSubTypes.cxx";
        file_input.cdr_aux_hpp_file = output_path_ + "/" + file_name_ + "CdrAux.hpp";
        file_input.cdr_aux_ipp_file = output_path_ + "/" + file_name_ + "CdrAux.ipp";
        file_input.h_output_file = output_path_ + "/" + file_name_ + "Temp.h";
        file_input.cpp_output_file = output_path_ + "/" + file_name_ + "Temp.cpp";

        std::vector<FileInput> file_inputs;
        file_inputs.push_back(file_input);
        return file_inputs;
    }

    void CleanupFiles(const FileInput &file_input) {
        // 删除临时文件
        fs::remove(file_input.h_file);
        fs::remove(file_input.pub_sub_types_h_file);

        fs::remove(file_input.cxx_file);
        fs::remove(file_input.pub_sub_cxx_file);
        fs::remove(file_input.cdr_aux_hpp_file);
        fs::remove(file_input.cdr_aux_ipp_file);

        // 将 temp 文件重命名为正式文件
        fs::rename(file_input.h_output_file, file_input.output_path + "/" + file_input.file_name + ".h");
        fs::rename(file_input.cpp_output_file, file_input.output_path + "/" + file_input.file_name + ".cpp");
    }

    void FormatFiles() {
        std::string header_file = output_path_ + "/" + file_name_ + ".h";
        std::string cpp_file = output_path_ + "/" + file_name_ + ".cpp";

        std::string command = "clang-format -i " + header_file + " --style=Google";
        system(command.c_str());

        command = "clang-format -i " + cpp_file + " --style=Google";
        system(command.c_str());
    }
};