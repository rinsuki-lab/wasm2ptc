#include <stdint.h>
__attribute__((import_name("print"))) void print(uint16_t* chars);

__attribute__((export_name("main")))
int main() {
    print(u"Hello, world from WASM!\n");
    return 0;
}