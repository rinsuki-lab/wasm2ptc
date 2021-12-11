use utf16_lit::{utf16_null};

extern {
    fn acls(x: u16);
    fn print(x: *const u16);
}

#[no_mangle]
pub unsafe extern fn main() {
    acls(0);
    print(utf16_null!("こんにちは\n").as_ptr());
}

