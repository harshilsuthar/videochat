FROM python:3.10.12-bullseye

RUN apt update -y
RUN apt upgrade -y

RUN pip3 install --upgrade pip

RUN mkdir /code/
RUN mkdir /code/logs

COPY ./requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

COPY ./ /code/

WORKDIR /code/

EXPOSE 8000

ENTRYPOINT ["sh", "entrypoint.sh"]
