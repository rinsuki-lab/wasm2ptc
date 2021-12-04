#include <stdint.h>
__attribute__((import_name("print"))) void print(const uint16_t* chars);
__attribute__((import_name("input_int32"))) int32_t input_int32(const uint16_t* message);

__attribute__((export_name("main")))
void main() {
    const uint16_t* aa[2] = {
        u"English Text", u"日本語text"
    };
    int32_t i = input_int32(u"0=eng, 1=jpn: ");
    if (i >= 2) {
        print(u"invalid...\n");
        return;
    }
    if (i < 0) {
        print(u"invalid2...\n");
        return;
    }
    print(aa[i]);
    print(u"\n");
}