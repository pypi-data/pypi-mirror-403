#include <booster/robot/rpc/rpc_client.hpp>
#include <booster/robot/x5_camera/x5_camera_client.hpp>

#include <chrono>
#include <thread>
#include <iostream>

using namespace booster::robot::x5_camera;

int main() {

    char input[256];
    int choice;
    int ret;
    
    ChannelFactory::Instance()->Init(0, "192.168.127.101");
    X5CameraClient client;
    client.Init();

    while (1) {
        printf("\nquery status: q, set mode: s\n");
        printf("Enter command (q/s) or 'e' to exit: ");
        
        if (fgets(input, sizeof(input), stdin) == NULL) {
            break;
        }
        
        input[strcspn(input, "\n")] = 0;
        
        if (strlen(input) == 0) {
            continue;
        }
        
        char command = input[0];
        
        switch (command) {
            case 'q':
            case 'Q':
                GetStatusResponse get_status_response;
                ret = client.GetStatus(get_status_response);
                printf("ret is %d\n", ret);
                printf("get_status_response is %d\n", get_status_response.status_);
                break;
                
            case 's':
            case 'S':
                printf("\n=== Set Mode ===\n");
                printf("0: normal\n");
                printf("1: high resolution\n");
                printf("2: normal enable\n");
                printf("3: high resolution enable\n");
                printf("Enter mode number (0-3): ");
                
                if (fgets(input, sizeof(input), stdin) == NULL) {
                    break;
                }
                
                choice = atoi(input);
                
                if (choice < 0 || choice > 3) {
                    printf("Invalid mode! Please enter 0-3.\n");
                } else {
                    ret = client.ChangeMode((CameraSetMode)choice);
                    printf("ret is %d\n", ret);
                }
                break;
                
            case 'e':
            case 'E':
                printf("Exiting...\n");
                return 0;
                
            default:
                printf("Invalid command! Please enter 'q' or 's'.\n");
                break;
        }
    }
}
    
