/**
 * Simomusu93-FW: misuratore della RAM libera minima. Vedi simomusu93_ram.cpp
 */
#pragma once
#include <stdint.h>

void     simomusu93_ram_paint();      // da chiamare il prima possibile all'avvio (inizio di setup())
uint32_t simomusu93_ram_free_min();   // byte di RAM mai usati da stack/heap dall'avvio a ora
uint32_t simomusu93_ram_painted();    // byte liberi al momento del riempimento
