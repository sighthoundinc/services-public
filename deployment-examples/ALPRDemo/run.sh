
# Remove all the sample app data before running, but keep the model cache
sudo mv ~/alprdemo ~/alprdemo.old
mkdir -p ~/alprdemo
sudo mv ~/alprdemo.old/.sio ~/alprdemo/
sudo rm -rf ~/alprdemo.old
# Run assuming nVidia runtime available. Running 2 live and 2 folder watch pipeline
# doesn't hold up with CPU-only inference
SIO_DOCKER_RUNTIME=nvidia docker compose up --build
