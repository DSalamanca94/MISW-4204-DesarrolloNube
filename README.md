# MISW-4204-DesarrolloNube

cd app
docker image build -t app .    
docker run -v /app/temp -p 5000:5000 -d app