#include <stdint.h>
__attribute__((import_name("print"))) void print(const uint16_t* chars);
__attribute__((import_name("input_int32"))) int32_t input_int32(const uint16_t* message);
__attribute__((import_name("vsync"))) void vsync(int32_t frame);
__attribute__((import_name("acls"))) void acls(int32_t dummy);
__attribute__((import_name("rnd"))) int32_t rnd(int32_t max);
__attribute__((import_name("beep"))) void beep(int32_t num);
__attribute__((import_name("button"))) int32_t button(int32_t max);

#define println(c) print(c"\n")

__attribute__((export_name("main")))
void main() {
    acls(0);
    println(u"");
    println(u"数当てゲーム");
    println(u"");
    println(u":ニコチャンが考えた");
    println(u"0〜99までの数字を当ててください");
    int32_t ans = rnd(100);
    while (1) {
        println(u"");
        int32_t no = input_int32(u"0〜99までの数字は");
        if (no < 0) continue;
        if (no > 99) continue;
        if (no == ans) {
            break;
        } else if (no < ans) {
            beep(4);
            println(u":HINT(大きいです)");
        } else {
            beep(6);
            println(u":HINT(小さいよ)");
        }
    }
    for (int i=0; i<50; i++) {
        print(u"");
    }
    println(u":当たり!!!!");
    println(u"PUSH  BUTTON");
    while (button(0) != 16) vsync(1);
}