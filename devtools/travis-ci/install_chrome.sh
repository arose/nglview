set -v

export CHROME_BIN=/usr/bin/google-chrome
# export DISPLAY=:99.0
# sh -e /etc/init.d/xvfb start

sudo apt-get install -y libappindicator1 fonts-liberation
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome*.deb
sudo apt-get install -f
sudo dpkg -i google-chrome*.deb
