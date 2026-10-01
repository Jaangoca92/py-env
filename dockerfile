#Usamos una imagen ultraligera de python compatible con 32 bits (i386)
FROM i386/python:3.8-slim

#Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el archivo de requerimientos
COPY requirements.txt

# Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del codigo fuente
COPY ..

# Exponemos el puerto en el que corre flask
EXPOSE 5000

# Variables de entorno para python
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar la aplicacion de forma profesional
CMD ["python", "app.py"]