#mmb - fork
This is a fork from the older original to make it more useful to my purposes.


##Initial commits:
* Get rid of pyMedia, it's outdated as all get out.
* Switch input to a FIFO buffer (feed from mpg123)
* Add arguments/commandline-ability


##Building
Looks like to get this going you must do two things:
###celt
Go in to the celt folder and run
`python ./setup.py build`
and copy the build *.so file to the main directory (you have to dig down in to the build folder).
###libcryptstate
Go in to the libcryptstate folder and run
`make` (simple, duh)
and copy the *.so file to the main directory.

From there it should all work.

##Running
`python ./main.py`
There's help in there so read that, it'll be kept more up to date. For a sample line:
`mpg123 -r 48000 -s "./somefile.mp3" | python ./main.py -s 127.0.0.1 -u username -p password`
###Piping and mpg123
mpg123 has just the right features to get us the PCM audio stream we need. It can also handle http streams:
`mpg123 -r 48000 -s "http://relay.radioreference.com:80/138151917"`
That will play the Boston Police radio feed from RadioReference.
* We _do_ need `-r 48000` because the celt encoder in our python script demands it (I've tried changing it, doesn't work).
* We _do_ need `-s` to get the stdout output.

##TODO
I want to get threshold detection going on the audio stream so we're not constantly broadcasting (useful in the case of voice streams).
