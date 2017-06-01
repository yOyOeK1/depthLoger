
t=`date +%y%m%d%H%M%S`

cd /home/yoyo/Backups/sony_opencpn
mkdir $t

echo "pull opencpn trax"
adb pull /sdcard/Android/data/org.opencpn.opencpn_free/files/navobj.xml "./"$t"/"
echo "	done"

echo "put fresh navobj to local dir"
cp "./"$t"/navobj.xml" /home/yoyo/.opencpn/
echo "	
done"


echo "push new charts"
adb push /home/yoyo/Charts/a_panama_bauhause/ /storage/sdcard1/Charts/a_panama_bsuhaus/
echo "	done"

echo "push gpx out of kap files"
adb push /home/yoyo/.opencpn/layers/depthOutOfSquers.gpx /sdcard/Android/data/org.opencpn.opencpn_free/files/layers/