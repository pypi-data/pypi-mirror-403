#pragma once

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <regex>
#include <iostream>
#include "helper.hpp"

class CppMerger {
public:
    std::string class_name_ = "";
    std::string cpp_file_ = "";
    std::string pub_sub_cpp_file_ = "";
    std::string output_file_ = "";

    int Merge(const std::string &cpp_file,
              const std::string &pub_sub_cpp_file,
              const std::string &output_file,
              const std::string &cdr_aux_hpp_file,
              const std::string &cdr_aux_ipp_file) {
        cpp_file_ = cpp_file;
        pub_sub_cpp_file_ = pub_sub_cpp_file;
        output_file_ = output_file;

        std::vector<std::string> cpp_content = ReadFile(cpp_file);
        std::vector<std::string> pub_sub_types_cpp_content = ReadFile(pub_sub_cpp_file);
        if (cpp_content.empty() || pub_sub_types_cpp_content.empty()) {
            std::cerr << "Error: One or both source files are empty or could not be read." << std::endl;
            return 1;
        }
        std::vector<std::string> merged_cpp_content = MergeFiles(cpp_content, pub_sub_types_cpp_content);
        if (merged_cpp_content.empty()) {
            std::cerr << "Error: Merging files failed." << std::endl;
            return 1;
        }

        std::vector<std::string> cdr_aux_hpp_content = ReadFile(cdr_aux_hpp_file);
        std::vector<std::string> cdr_aux_ipp_content = ReadFile(cdr_aux_ipp_file);
        if (cdr_aux_hpp_content.empty() || cdr_aux_ipp_content.empty()) {
            std::cerr << "Error: One or both CDR aux files are empty or could not be read." << std::endl;
            return 1;
        }
        std::vector<std::string> merged_content = MergeCdrAuxFiles(merged_cpp_content, cdr_aux_hpp_content, cdr_aux_ipp_content);
        if (merged_content.empty()) {
            std::cerr << "Error: Merging CDR aux files failed." << std::endl;
            return 1;
        }
        WriteFile(output_file, merged_content);
        std::cout << "CPP Files " << cpp_file << " and " << pub_sub_cpp_file
                  << " have been merged into " << output_file << std::endl;

        return 0;
    }

    std::vector<std::string> MergeCdrAuxFiles(
        const std::vector<std::string> &cpp_merged_content,
        const std::vector<std::string> &cdr_aux_hpp_file,
        const std::vector<std::string> &cdr_aux_ipp_file) {
        // 找到 aux hpp 里两个常量定义 constexpr uint32_t
        std::string pattern = "constexpr uint32_t ";
        int first_const_idx = FindLineIndex(cdr_aux_hpp_file, pattern);
        if (first_const_idx == -1) {
            std::cerr << "Error: Could not find first const in cdr aux hpp file." << std::endl;
            return std::vector<std::string>();
        }
        int second_const_idx = first_const_idx + 1;

        std::vector<std::string> aux_const_content;
        aux_const_content.push_back(cdr_aux_hpp_file[first_const_idx]);
        aux_const_content.push_back(cdr_aux_hpp_file[second_const_idx]);

        std::vector<std::string> merged_content = cpp_merged_content;
        // merged_content 里找到 .ipp"
        pattern = ".ipp\"";
        int ipp_idx = FindLineIndex(merged_content, pattern);
        if (ipp_idx == -1) {
            std::cerr << "Error: Could not find .ipp in cpp merged content." << std::endl;
            return std::vector<std::string>();
        }
        merged_content.erase(merged_content.begin() + ipp_idx);
        merged_content.insert(merged_content.begin() + ipp_idx, aux_const_content.begin(), aux_const_content.end());

        // 在 ipp 里找到 ”#include <fastcdr/Cdr.h>“
        pattern = "#include <fastcdr/Cdr.h>";
        int include_idx = FindLineIndex(cdr_aux_ipp_file, pattern);
        pattern = "endif";
        int endif_idx = FindLineIndex(cdr_aux_ipp_file, pattern);
        if (include_idx == -1 || endif_idx == -1) {
            std::cerr << "Error: Could not find include cdr or endif in cdr aux ipp file." << std::endl;
            return std::vector<std::string>();
        }

        std::vector<std::string> aux_ipp_content;
        aux_ipp_content.insert(aux_ipp_content.end(), cdr_aux_ipp_file.begin() + include_idx, cdr_aux_ipp_file.begin() + endif_idx);
        merged_content.insert(merged_content.begin() + ipp_idx + 2, aux_ipp_content.begin(), aux_ipp_content.end());

        return merged_content;
    }

    std::vector<std::string> MergeFiles(
        std::vector<std::string> &cpp_content,
        std::vector<std::string> &pub_sub_types_cpp_content) {
        int res = PreprocessCppContent(cpp_content);
        if (res != 0) {
            std::cerr << "Error: Preprocessing cpp content failed." << std::endl;
            return std::vector<std::string>();
        }
        res = PreprocessPubSubTypesCppContent(pub_sub_types_cpp_content);
        if (res != 0) {
            std::cerr << "Error: Preprocessing pub sub types cpp content failed." << std::endl;
            return std::vector<std::string>();
        }
        std::vector<std::string> merged_content;
        merged_content.insert(merged_content.end(), cpp_content.begin(), cpp_content.end());
        merged_content.insert(merged_content.end(), pub_sub_types_cpp_content.begin(), pub_sub_types_cpp_content.end());
        return merged_content;
    }

    int PreprocessCppContent(std::vector<std::string> &cpp_content) {
        std::string pattern = class_name_ + "::" + class_name_ + "()";
        int constructor_idx = FindLineIndex(cpp_content, pattern);
        // 移除掉第一个构造函数
        if (constructor_idx == -1) {
            std::cerr << "Error: Could not find constructor in cpp file. pattern = " << pattern << std::endl;
            return -1;
        }
        int first_bracket_idx = FindLineIndex(cpp_content, "}", constructor_idx);
        if (first_bracket_idx == -1) {
            std::cerr << "Error: Could not find closing bracket of constructor in cpp file." << std::endl;
            return -1;
        }
        cpp_content.erase(cpp_content.begin() + constructor_idx, cpp_content.begin() + first_bracket_idx + 1);

        int deconstructor_idx = FindLineIndex(cpp_content, class_name_ + "::~" + class_name_ + "()");
        // 移除掉第一个析构函数
        if (deconstructor_idx == -1) {
            std::cerr << "Error: Could not find deconstructor in cpp file." << std::endl;
            return -1;
        }
        int second_bracket_idx = FindLineIndex(cpp_content, "}", deconstructor_idx);
        if (second_bracket_idx == -1) {
            std::cerr << "Error: Could not find closing bracket of deconstructor in cpp file." << std::endl;
            return -1;
        }
        cpp_content.erase(cpp_content.begin() + deconstructor_idx, cpp_content.begin() + second_bracket_idx + 1);
        // 找到第一个 const CLASS_NAME& x)
        int copy_constructor_idx = FindLineIndex(cpp_content, "const " + class_name_ + "& x)");
        // 在这一行后面添加 ": CLASS_NAME()"，即调用默认构造函数
        if (copy_constructor_idx == -1) {
            std::cerr << "Error: Could not find copy constructor in cpp file." << std::endl;
            return -1;
        }
        auto &line = cpp_content[copy_constructor_idx];
        line += " : " + class_name_ + "()";
        // 找到第一个 CLASS_NAME&& x) noexcept
        int move_constructor_idx = FindLineIndex(cpp_content, class_name_ + "&& x) noexcept");
        // 在这一行后面添加 ": CLASS_NAME()"，即调用默认构造函数
        if (move_constructor_idx == -1) {
            std::cerr << "Error: Could not find move constructor in cpp file." << std::endl;
            return -1;
        }
        auto &move_line = cpp_content[move_constructor_idx];
        move_line += " : " + class_name_ + "()";
        return 0;
    }


    int PreprocessPubSubTypesCppContent(std::vector<std::string> &pub_sub_types_cpp_content) {
        std::string replace_pattern = class_name_ + "PubSubType";
        for (auto &line : pub_sub_types_cpp_content) {
            std::regex inlude_pbtypes_pattern(R"(#include\s+"(\w+)PubSubTypes\.h")");
            if (std::regex_search(line, inlude_pbtypes_pattern)) {
                line = std::regex_replace(line, inlude_pbtypes_pattern, "");
            }

            std::regex include_cdr_pattern(R"(#include\s+"(\w+)CdrAux\.hpp")");
            if (std::regex_search(line, include_cdr_pattern)) {
                line = std::regex_replace(line, include_cdr_pattern, "");
            }

            std::regex pattern(replace_pattern);
            line = std::regex_replace(line, pattern, class_name_);
        }

        replace_pattern = "::" + class_name_ + "\"";
        int msg_name_idx = FindLineIndex(pub_sub_types_cpp_content, replace_pattern);
        if (msg_name_idx == -1) {
            std::cerr << "Error: Could not find message name in pub sub types cpp file." << std::endl;
            return -1;
        }
        auto &msg_name_line = pub_sub_types_cpp_content[msg_name_idx];
        msg_name_line = std::regex_replace(msg_name_line, std::regex(replace_pattern), "::dds_::" + class_name_ + "_\"");

        return 0;
    }
};