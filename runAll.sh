sudo docker rm -f $(sudo docker ps -a -q --filter="ancestor=snommd");
sudo bash build.sh;sudo docker kill $(sudo docker ps -a -q --filter="ancestor=snommd");  sudo bash run.sh
