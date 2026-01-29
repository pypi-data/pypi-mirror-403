#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <regex>

#include "merger.hpp"
#include "dds_file_manager.hpp"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: booster_fastdds_gen <file_path>" << std::endl;
        return 1;
    }

    std::string file_path = argv[1];
    if (file_path.empty()) {
        std::cerr << "Error: File path is empty." << std::endl;
        return 1;
    }

    DdsFileManager file_manager;
    int res = file_manager.Init(file_path);
    if (res != 0) {
        std::cerr << "Error: Failed to init dds file manager." << std::endl;
        return 1;
    }
    file_manager.CleanupPreviousGeneratedFiles();
    res = file_manager.GenerateDdsFiles();
    if (res != 0) {
        std::cerr << "Error: Failed to generate DDS files." << std::endl;
        return 1;
    }
    std::vector<FileInput> file_inputs = file_manager.ReadDdsGenFiles();
    if (file_inputs.empty()) {
        std::cerr << "Error: No DDS files found in path: " << file_path << std::endl;
        return 1;
    }
    for (const FileInput &file_input : file_inputs) {
        Merger merger(file_input);
        int res = merger.Merge();
        // 删除临时文件
        if (res == 0) {
            file_manager.CleanupFiles(file_input);
        }
    }
    file_manager.FormatFiles();

    std::cout << "\nBooster FastDDS generated successfully." << std::endl;

    return 0;
}
