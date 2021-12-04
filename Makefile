a.ptc: a.ptc.txt txt2ptc.py
	python3 txt2ptc.py $< $@
	cp $@ '${HOME}/.local/share/citra-emu/sdmc/Nintendo 3DS/00000000000000000000000000000000/00000000000000000000000000000000/extdata/00000000/00001172/user/###/TA.OUT'

a.ptc.txt: a.wat wat2bas.py
	python3 wat2bas.py $< $@

a.wat: a.wasm
	wasm2wat $< -o $@

a.wasm: a.o
	/usr/local/opt/llvm/bin/wasm-ld -o $@ --no-entry $< 
	# wasm-strip $@

a.o: a.c
	/usr/local/opt/llvm/bin/clang -c -Os --target=wasm32-wasm -o $@ $<

clean:
	rm a.ptc a.ptc.txt a.wat a.wasm