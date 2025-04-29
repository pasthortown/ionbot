FROM python:3.8

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN fc-cache -f -v

COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN echo "America/Bogota" > /etc/timezone

COPY ./imagenes ./imagenes
COPY image_gen.py .
COPY tournament.py .
COPY api_manager.py .
COPY script_docker.py script.py

CMD [ "python", "script.py" ]