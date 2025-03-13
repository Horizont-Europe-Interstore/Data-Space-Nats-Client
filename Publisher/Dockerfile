FROM python:3.11.2-alpine

WORKDIR /app

EXPOSE 5030

COPY . /app
RUN apk update && apk add gcc libpq-dev 
 RUN  pip install --upgrade pip 
    RUN pip install -r requirements.txt


CMD [ "python","-u", "pub.py" ]