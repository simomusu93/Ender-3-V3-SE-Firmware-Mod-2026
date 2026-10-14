#pragma once
#include <stdint.h>
struct CardReader {
  static FILE *f; static long size, pos; static bool printing;
  static void openFileRead(const char *p){ f=fopen(p,"rb"); if(f){fseek(f,0,SEEK_END);size=ftell(f);fseek(f,0,SEEK_SET);pos=0;} }
  static bool isFileOpen(){ return f!=nullptr; }
  static bool isPrinting(){ return printing; }
  static bool eof(){ return pos>=size; }
  static int16_t get(){ int c=fgetc(f); if(c!=EOF) pos++; return c==EOF?-1:c; }
  static void closefile(){ if(f) fclose(f); f=nullptr; }
};
extern CardReader card;
