all:
	g++ -c -fPIC CryptState.cpp -o cryptstate.o 
	g++ -shared -Wl,-soname,libcryptstate.so -o libcryptstate.so  cryptstate.o -lssl

clean:
	rm *.{o,so}
