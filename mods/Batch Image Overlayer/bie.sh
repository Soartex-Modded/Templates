#!/bin/bash

### Make sure imagemagick is installed ###
if type -P convert &>/dev/null; then
        echo "imagemagic found continuing..."
    else
        echo "imagemagic NOT installed quiting..."
        exit
fi
### Get current directory ###
CWD=$(pwd)
echo "Starting directory is:" $CWD
### Set input image directory ###
IID="$CWD/input"
echo "Input directory is:" $IID
### Directory checking ###
mkdir -p $CWD/convert; mkdir -p $CWD/input; mkdir -p $CWD/output;
### Check convert directory for images and if existent copy top output ###
if [ ! "$(ls -A $CWD/convert)" ]; then
    printf "Convert folder is empty,\nPlease add images to convert and run again\nExiting..."
    exit
fi
### Check input folder for images ###
if [ ! "$(ls -A $CWD/input)" ]; then
    printf "Input folder is empty,\nPlease add images to input and run again\nExiting..."
    exit
fi
### (I)tterate (A)nd (C)onvert function ###
### Overlay is currently embeded I'll make it external later ###
func_iac () {
            ### Iterate through CONVERT directory for PNG files ###
            for file in $(find $CWD/convert -name '*.png'); do
                echo "Found PNG: "$file;
                ### Get image path ###
                FDIR=$(dirname $file)
                ### Get image name ###
                IMAGENAME=$(basename $file)
                NIP=${FDIR//convert/output}
                mkdir -p $NIP
                ## ACTUAL PROCESSING OF IMAGES HERE ###
                convert $file \
                        \( +clone $IID/$SOURCEIMAGE -alpha on -compose overlay -composite \) \
                        -compose In -composite "$NIP/$SOURCESTRIPPED"_"$IMAGENAME"
                echo "Outputted: $NIP/$SOURCESTRIPPED"_"$IMAGENAME"
            done
}
### Iterate through INPUT directory for PNG files ###
for ii in $IID/* ; do
    if [[ $ii == *.png ]]; then
        ### Strip path from filename ###
        SOURCEIMAGE=$(basename $ii)
        ### Strip extension for appending name ###
        SOURCESTRIPPED="${SOURCEIMAGE%.*}"
        echo "PNG found: "$SOURCEIMAGE "Stripped  name: " $SOURCESTRIPPED
        func_iac
    fi
done
