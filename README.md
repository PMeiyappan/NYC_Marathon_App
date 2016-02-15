
# NYC Marathon App





####Dependencies




* ubuntu/apt-get
  * libatlas-base-dev
  * gfortran
  * python-dev
  * build-essential
  * g++
  * python-pip

* python 2.x/pip
  * flask
  * numpy
  * scipy
  * sklearn
  * pandas


#####Instructions for ubuntu if you run out of memory

```
#creates a large swapfile of 4GB
sudo fallocate -l 4G /swapfile

#makes it unreadable for bad guys
sudo chmod 600 /swapfile

#make it into a swap file
sudo mkswap /swapfile

#activate the swap file
sudo swapon /swapfile

#optionally turn it off
sudo swapoff /swapfile
#optionally remove it
sudo rm /swapfile

#if you want to make the swap file permanent,
# see https://www.digitalocean.com/community/tutorials/how-to-add-swap-on-ubuntu-14-04
# section "Make the Swap File Permanent"

```



