#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/select.h>

#define BACKLOG 512
#define MAX_MESSAGE_LEN 2048

void error(const char* msg);

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Please give a port number: ./select_echo_server [port]\n");
        exit(0);
    }

    // some variables we need
    int portno = strtol(argv[1], NULL, 10);
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);

    char buffer[MAX_MESSAGE_LEN];
    memset(buffer, 0, sizeof(buffer));

    // setup socket
    int sock_listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (sock_listen_fd < 0) {
        error("Error creating socket..\n");
    }

    memset((char *)&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(portno);
    server_addr.sin_addr.s_addr = INADDR_ANY;

    // bind socket and listen for connections
    if (bind(sock_listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)
        error("Error binding socket..\n");

    if (listen(sock_listen_fd, BACKLOG) < 0) {
        error("Error listening..\n");
    }
    printf("select echo server listening for connections on port: %d\n", portno);

    fd_set master_set, read_fds;
    int fdmax = sock_listen_fd;

    FD_ZERO(&master_set);
    FD_ZERO(&read_fds);

    FD_SET(sock_listen_fd, &master_set);

    while (1) {
        read_fds = master_set;

        if (select(fdmax + 1, &read_fds, NULL, NULL, NULL) == -1) {
            error("Error in select..\n");
        }

        for (int i = 0; i <= fdmax; i++) {
            if (FD_ISSET(i, &read_fds)) {
                if (i == sock_listen_fd) {
                    // handle new connections
                    int new_fd = accept(sock_listen_fd, (struct sockaddr *)&client_addr, &client_len);
                    if (new_fd == -1) {
                        error("Error accepting new connection..\n");
                    } else {
                        FD_SET(new_fd, &master_set);
                        if (new_fd > fdmax) {
                            fdmax = new_fd;
                        }
                    }
                } else {
                    // handle data from a client
                    int nbytes = recv(i, buffer, sizeof(buffer), 0);
                    if (nbytes <= 0) {
                        if (nbytes == 0) {
                            printf("select server: socket %d hung up\n", i);
                        } else {
                            perror("recv");
                        }
                        close(i);
                        FD_CLR(i, &master_set);
                    } else {
                        send(i, buffer, nbytes, 0);
                    }
                }
            }
        }
    }

    return 0;
}

void error(const char* msg) {
    perror(msg);
    exit(1);
}