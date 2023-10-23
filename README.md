# MISW-4204-DesarrolloNube

# Guía para ejecutar la aplicación con Docker

Esta guía te mostrará cómo ejecutar la aplicación en EL contenedor Docker.

## Requisitos previos
- Docker debe estar instalado en tu sistema. Puedes obtener Docker en [docker.com](https://www.docker.com/get-started).

## Pasos

### 1. Clonar el repositorio

### 2. Navegar al directorio de la aplicación

cd app

### 3. Construir la imagen Docker

docker image build -t app .

### 3. Construir el contenedor 

docker run -v /app/temp -p 5000:5000 -d app