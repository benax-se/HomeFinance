FROM python:3.10.0
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY req.txt /code/
RUN pip install -r req.txt

COPY . /code/
#RUN ["chmod", "+x" ,"/code/docker-entrypoint.sh"]

#ENTRYPOINT [ "/code/docker-entrypoint.sh" ]