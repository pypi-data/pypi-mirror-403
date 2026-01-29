#pragma once

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <regex>
#include <iostream>
#include "helper.hpp"

class HeaderMerger {
public:
    std::string class_name_ = "";
    std::string hpp_file_ = "";
    std::string pub_sub_hpp_file_ = "";
    std::string output_file_ = "";

    int Merge(const std::string &hpp_file,
              const std::string &pub_sub_hpp_file,
              const std::string &output_file) {
        hpp_file_ = hpp_file;
        pub_sub_hpp_file_ = pub_sub_hpp_file;
        output_file_ = output_file;

        std::vector<std::string> hpp_header_content = ReadFile(hpp_file);
        std::vector<std::string> pub_sub_types_hpp_content = ReadFile(pub_sub_hpp_file);

        if (hpp_header_content.empty() || pub_sub_types_hpp_content.empty()) {
            std::cerr << "Error: One or both source files are empty or could not be read." << std::endl;
            return 1;
        }

        std::vector<std::string> merged_content = MergeFiles(hpp_header_content, pub_sub_types_hpp_content);
        PostProcess(merged_content);

        if (!merged_content.empty()) {
            WriteFile(output_file, merged_content);
            std::cout << "Files " << hpp_file << " and " << pub_sub_hpp_file
                      << " have been merged into " << output_file << std::endl;
        } else {
            std::cerr << "Error: Merging files failed." << std::endl;
            return 1;
        }
        return 0;
    }

    void PostProcess(std::vector<std::string> &merged_content) {
        std::string remove_pattern = "#include \"" + class_name_ + ".h\"";
        for (auto &line : merged_content) {
            if (line.find(remove_pattern) != std::string::npos) {
                line = "";
                continue;
            }
            std::regex inlude_pbtypes_pattern(R"(#include\s+"(\w+)PubSubTypes\.h")");
            if (std::regex_search(line, inlude_pbtypes_pattern)) {
                line = "";
                continue;
            }
        }
    }

    std::vector<std::string> PreprocessClassContent(std::vector<std::string> &class_content_lines, const std::string &class_name) {
        std::vector<std::string> cutted_content;

        // 找到第二个 "();" 的位置
        int func_end_idx = FindLineIndex(class_content_lines, "();", 1);
        cutted_content.insert(cutted_content.end(), class_content_lines.begin(), class_content_lines.begin() + func_end_idx - 3);
        func_end_idx = FindLineIndex(class_content_lines, "();", func_end_idx + 1);
        cutted_content.insert(cutted_content.end(), class_content_lines.begin() + func_end_idx + 1, class_content_lines.end());
        return cutted_content;
    }

    std::vector<std::string> PreprocessPubSubContent(std::vector<std::string> &pub_sub_content_lines, const std::string &class_name) {
        std::vector<std::string> cutted_content;
        std::string pub_sub_class_name;
        std::regex class_name_regex(R"(class\s+(\w+))");
        std::smatch match;

        int idx = 0;
        // 找到 class 的名字，同时在 class 那一行的末尾插入 ": public eprosima::fastdds::dds::TopicDataType"
        bool is_skip = false;
        for (auto &line : pub_sub_content_lines) {
            idx++;
            std::string trimmed_line = line;
            trimmed_line.erase(0, trimmed_line.find_first_not_of(" \t"));
            // std::cout << "trimmed_line: " << trimmed_line << std::endl;
            if (trimmed_line.rfind("/*", 0) == 0) {
                is_skip = true;
                // std::cout << "skip start" << std::endl;
                continue;
            }
            if (is_skip) {
                if (trimmed_line.rfind("*/", 0) == 0) {
                    is_skip = false;
                    // std::cout << "skip end" << std::endl;
                }
                continue;
            }
            if (trimmed_line.rfind("//", 0) == 0) {
                continue;
            }
            if (std::regex_search(line, match, class_name_regex)) {
                // 获取这一行的 idx
                pub_sub_class_name = match[1];
                break;
            }
        }
        // 从 idx - 1 开始找到第一个 "{" 的位置
        int class_start_idx = FindLineIndex(pub_sub_content_lines, "{", idx - 1) + 1;
        if (class_start_idx == 0) {
            std::cerr << "Error: Could not find class start in pubSub content." << std::endl;
            return cutted_content;
        }
        int class_end_idx = FindLineIndex(pub_sub_content_lines, "};", class_start_idx);
        if (class_end_idx == 0) {
            std::cerr << "Error: Could not find class end in pubSub content." << std::endl;
            return cutted_content;
        }
        cutted_content.insert(cutted_content.end(), pub_sub_content_lines.begin() + class_start_idx, pub_sub_content_lines.begin() + class_end_idx - 1);
        for (auto &line : cutted_content) {
            // 遍历每一行行，将遇到的 pub_sub_class_name 替换为 class_name
            std::regex pub_sub_type_regex(pub_sub_class_name);
            line = std::regex_replace(line, pub_sub_type_regex, class_name);
        }

        return cutted_content;
    }

    // Function to merge class definitions
    std::vector<std::string> MergeClasses(std::vector<std::string> &class_content_lines, std::vector<std::string> &pub_sub_content_lines) {
        std::vector<std::string> merged_content;
        std::regex class_name_regex(R"(class\s+(\w+))");
        std::smatch match;

        // Find class name
        // 找到 class 的名字，同时在 class 那一行的末尾插入 ": public eprosima::fastdds::dds::TopicDataType"
        bool is_skip = false;
        for (auto &line : class_content_lines) {
            std::string trimmed_line = line;
            trimmed_line.erase(0, trimmed_line.find_first_not_of(" \t"));
            // std::cout << "trimmed_line: " << trimmed_line << std::endl;
            if (trimmed_line.rfind("/*", 0) == 0) {
                is_skip = true;
                // std::cout << "skip start" << std::endl;
                continue;
            }
            if (is_skip) {
                if (trimmed_line.rfind("*/", 0) == 0) {
                    is_skip = false;
                    // std::cout << "skip end" << std::endl;
                }
                continue;
            }

            if (trimmed_line.rfind("//", 0) == 0) {
                continue;
            }

            if (std::regex_search(line, match, class_name_regex)) {
                class_name_ = match[1];
                std::string replace_content = "class " + class_name_ + " : public eprosima::fastdds::dds::TopicDataType";
                line = std::regex_replace(line, class_name_regex, replace_content);
                std::cout << "class_name: " << class_name_ << std::endl;
                break;
            }
        }

        if (class_name_.empty()) {
            std::cerr << "Error: Could not find class name in class content." << std::endl;
            return merged_content;
        }

        // merged_content 插入所有 class_content_lines 的内容
        class_content_lines = PreprocessClassContent(class_content_lines, class_name_);
        merged_content.insert(merged_content.end(), class_content_lines.begin(), class_content_lines.end());

        // 找到 class_content_lines 中的 private:
        int private_section_idx = FindLineIndex(class_content_lines, "private:") + 1;
        if (private_section_idx == 0) {
            std::cerr << "Error: Could not find private section in class content." << std::endl;
            return merged_content;
        }

        // 找到 class_name 后寻找第一个 "};" 的位置
        int class_end_idx = FindPrefixLineIndex(class_content_lines, "};", private_section_idx);
        if (class_end_idx == 0) {
            std::cerr << "Error: Could not find class end in class content." << std::endl;
            return merged_content;
        }

        // 在 class_end_idx 前插入 pub_sub_content_lines 的内容
        auto cutted_content = PreprocessPubSubContent(pub_sub_content_lines, class_name_);
        merged_content.insert(merged_content.begin() + class_end_idx, cutted_content.begin(), cutted_content.end());
        return merged_content;
    }

    // Function to merge the contents of two files
    std::vector<std::string> MergeFiles(const std::vector<std::string> &hpp_header,
                                        const std::vector<std::string> &pub_sub_types_hpp_header) {
        std::vector<std::string> merged_content;

        int include_guard_idx = FindLineIndex(hpp_header, "#include <fastcdr/xcdr/optional.hpp>") + 1;
        int namespace_end_idx = FindLineIndex(hpp_header, "} // namespace eprosima") + 1;
        int public_section_idx = FindLineIndex(hpp_header, "public:") + 1;

        if (include_guard_idx == 0 || namespace_end_idx == 0 || public_section_idx == 0) {
            std::cerr << "Error: Could not find required sections in .h" << std::endl;
            return merged_content;
        }

        merged_content.insert(merged_content.end(), hpp_header.begin(), hpp_header.begin() + include_guard_idx);
        merged_content.push_back("\n// ------------------------------ Pub Sub Type Start ----------------------------\n");

        int pub_sub_include_start_idx = FindLineIndex(pub_sub_types_hpp_header, "#include <fastdds/dds/core/policy/QosPolicies.hpp>");
        int pub_sub_gen_api_ver_end_idx = FindLineIndex(pub_sub_types_hpp_header, "#endif  // GEN_API_VER") + 1;
        if (pub_sub_include_start_idx == -1 || pub_sub_gen_api_ver_end_idx == 0) {
            std::cerr << "Error: Could not find required sections in TestPubSubTypes.h" << std::endl;
            return merged_content;
        }
        merged_content.insert(merged_content.end(), pub_sub_types_hpp_header.begin() + pub_sub_include_start_idx, pub_sub_types_hpp_header.begin() + pub_sub_gen_api_ver_end_idx);
        merged_content.push_back("\n// ------------------------------ Pub Sub Type End ----------------------------\n");
        merged_content.insert(merged_content.end(), hpp_header.begin() + include_guard_idx, hpp_header.begin() + namespace_end_idx);
        // 获取 hpp_header 当前剩余的内容
        std::vector<std::string> class_content_lines = std::vector<std::string>(hpp_header.begin() + namespace_end_idx, hpp_header.end());

        // 获取 pub_sub_types_hpp_header 当前剩余的内容
        std::vector<std::string> pub_sub_content_lines = std::vector<std::string>(pub_sub_types_hpp_header.begin() + pub_sub_gen_api_ver_end_idx, pub_sub_types_hpp_header.end());

        auto merged_classes = MergeClasses(class_content_lines, pub_sub_content_lines);

        merged_content.insert(merged_content.end(), merged_classes.begin(), merged_classes.end());

        return merged_content;
    }
};