#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <pthread.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <sys/stat.h>

int clientNum = 0;
struct client {
    int cfd;
    struct sockaddr_in clientAddr;
    char name[32];
    int id;
    int len;

};

struct client client[1024];
pthread_t thread[1024];

//Watek dla kazdego zalogowanego uzytkownika
void *cthread(void *ClientDetail) {

    struct client *clientDetail = (struct client *) ClientDetail;
    char username[32];
    strncpy(username, clientDetail->name, 32);
    int id = clientDetail->id;
    int clientSocket = clientDetail->cfd;

    printf("Client %d connected.\n", id + 1);

    while (1) {

        char data[1024];
        char *command, *datarest;
        int read = recv(clientSocket, data, 1024, 0);
        data[read] = '\0';
        //char output[1024];

        if (read == 0) continue;
        //Wydzielenie pierwszego slowa - komendy
        char *ptrdata = data;
        command = strtok_r(ptrdata, " ", &datarest);

        //SEND - wiadomosci
        if (strcmp(command, "SEND") == 0) {
            char *ptrrecipent = strtok_r(datarest, " ", &datarest);
            char recipent[32];
            strncpy(recipent, ptrrecipent, 32);
            int logged = 0;

            //sprawdz czy uzytkownik jest dostepny
            for (int i = 0; i < clientNum; i++) {
                if (strcmp(recipent, client[i].name) == 0) {
                    if (client[i].cfd != 0) logged = i + 1;
                }
            }
            if (logged > 0) {
                send(client[logged - 1].cfd, datarest, strlen(datarest), 0);
            } else {
                //zapis wiadomosci dla uzytkownika offline
                char loc[128] = "./serverData/";
                strcat(loc, recipent);

                FILE *file = fopen(loc, "a");
                fprintf(file, "%s\n", datarest);
                fclose(file);
            }
        }

        //Login
        if (strcmp(command, "LOGIN") == 0) {
            printf("User %s online\n", datarest);
            strncpy(client[id].name, datarest, 32);

            //Sprawdz czy uzytkownik nie ma zadnych nieprzeczytanych wiadomosci
            char loc[128] = "./serverData/";
            char owner[32];
            strcpy(owner, client[id].name);
            strcat(loc, owner); //plik z nieodebranymi wiadomosciami

            char line[1024];
            ssize_t line_size;
            char *line_buf = NULL;
            size_t line_buf_size = 0;
            FILE *file = fopen(loc, "r");
            if (file == NULL) continue;
            line_size = getline(&line_buf, &line_buf_size, file);
            while (line_size >= 0) {
                //przygotowanie wiadomosci, wysylanie
                strcpy(line, "");
                strcat(line, line_buf);

                send(client[id].cfd, line, strlen(line), 0);
                line_size = getline(&line_buf, &line_buf_size, file);
                usleep(500000); //sleep 0.5s - poprawa plynnosci
            }
            //Remove log of due messages
            remove(loc);
            fclose(file);
        }
        //Wylogowanie z systemu, oznaczenie uzytkownika jako offline
        if (strcmp(command, "DEAD") == 0) {
            close(client[id].cfd);
            client[id].cfd = 0;
            printf("User %s disconnected\n", client[id].name);
            sleep(500000);
            break;
        }

    }

    pthread_join(thread[id], NULL);
    return NULL;

}

int main(void) {
    //Inicjalizacja socketow
    int serverSocket = socket(PF_INET, SOCK_STREAM, 0);

    struct sockaddr_in serverAddr;

    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(1234);
    serverAddr.sin_addr.s_addr = htons(INADDR_ANY);
    if (bind(serverSocket, (struct sockaddr *) &serverAddr, sizeof(serverAddr)) == -1) return 0;
    //listen
    if (listen(serverSocket, 1024) == -1) return 0;

    printf("Server is up\n");

    //Utworz folder w celu rejestrowania wiadomosci
    struct stat st = {0};

    if (stat("./serverData", &st) == -1) {
        mkdir("./serverData", 0777);
    }
    //Tworzenie nowych watkow
    while (1) {
        unsigned int c = client[clientNum].len;
        client[clientNum].cfd = accept(serverSocket, (struct sockaddr *) &client[clientNum].clientAddr, &c);
        client[clientNum].id = clientNum;
        pthread_create(&thread[clientNum], NULL, cthread, (void *) &client[clientNum]);
        clientNum++;

    }
    //zamknij wszystko
    for (int i = 0; i < clientNum; i++)
        pthread_join(thread[i], NULL);
    close(serverSocket);

}