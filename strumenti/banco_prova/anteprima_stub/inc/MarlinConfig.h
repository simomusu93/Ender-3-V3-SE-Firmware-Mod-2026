#pragma once
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define ENABLED(x) 1
#define TEST(n,b) (((n)>>(b))&1)
#define SBI(n,b) ((n)|=(1<<(b)))
#define FILENAME_LENGTH 260   // sul PC il "nome" è un percorso completo; sulla stampante è un nome 8.3 (13)
void delay(unsigned long);
void HAL_watchdog_refresh();
