#pragma once

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <regex>
#include <iostream>

// Function to read file contents into a vector of strings
std::vector<std::string> ReadFile(const std::string &filename) {
    std::vector<std::string> lines;
    std::ifstream file(filename);
    if (file.is_open()) {
        std::string line;
        while (std::getline(file, line)) {
            lines.push_back(line + '\n');
        }
        file.close();
    } else {
        std::cerr << "Unable to open file: " << filename << std::endl;
    }
    return lines;
}

void PrintContent(const std::vector<std::string> &content) {
    std::cout << "Start print content ----------" << std::endl;
    for (auto line : content) {
        std::cout << line << std::endl;
    }
    std::cout << "End print content ----------" << std::endl;
}

// Function to write a vector of strings to a file
void WriteFile(const std::string &filename, const std::vector<std::string> &content) {
    std::ofstream file(filename);
    if (file.is_open()) {
        for (const auto &line : content) {
            file << line;
        }
        file.close();
    } else {
        std::cerr << "Unable to open file: " << filename << std::endl;
    }
}

// Function to find the index of a specific line in a vector of strings
int FindLineIndex(const std::vector<std::string> &content, const std::string &target, int start_idx = 0) {
    for (size_t i = start_idx; i < content.size(); ++i) {
        if (content[i].find(target) != std::string::npos) {
            return i;
        }
    }
    return -1;
}

int FindPrefixLineIndex(const std::vector<std::string> &content, const std::string &target, int start_idx = 0) {
    for (size_t i = start_idx; i < content.size(); ++i) {
        if (content[i].find(target) == 0) {
            return i;
        }
    }
    return -1;
}
