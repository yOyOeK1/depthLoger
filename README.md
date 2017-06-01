# depthLoger
Hello.
This is a depthLoger repository.
It is an app for collecting, processing and then puting new readings of depth on to kap charts files. All and more is done automaticlly.
For now it is in earlly stage of development but it is working app.

App in using python and five third party libraries.
It records or import nmea data from gpsd or nmea log files, store the data in sqlite database and then after processing, making an offsets, uncluging putting new values on kap charts or generate gpx file. 


To make it working:
- clone repository to your local mashine
- run ./build.sh
- edit config ( ./depthLoger.py ~from line 25 ) or run it with correct arguments 
    try to run ./depthLoger.py --help
- download or import data from nmea logs
    you can find my database at https://github.com/yOyOeK1/depthLogerDB
- set up your source kap file directory

Example of work

original file
![Alt text](./imgs/kapTmp.kap.png?raw=true "Before")

after work
![Alt text](./imgs/kapTmp.kap_mod.png?raw=true "After")


more detail destription comming soon...
cdn... :)
