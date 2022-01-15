# base image
FROM python:3

# fix bug with pymssql
RUN apt update && \
	apt-get install freetds-dev -y && \
    apt install --no-install-recommends -y build-essential gcc && \
    apt clean && rm -rf /var/lib/apt/lists/*

# set a directory for the app
WORKDIR /root/container/telebot

# copy all the files to the container
COPY . .

# install pip
RUN pip3 install --upgrade pip
# install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# tell the port number the container should expose
EXPOSE 5000

# set os variables
ARG HOSTNAME="<YOUR DATABASE>"
ARG USERNAME="<YOUR USERNAME>"
ARG PASSWORD="<YOUR PASSWORD>"

# create the ability to change during the build
ENV DB_HOST=$HOSTNAME
ENV DB_USER=$USERNAME
ENV DB_PWD=$PASSWORD

# to make run.sh executable
RUN chmod a+x run.sh

# run the main command
CMD ["./run.sh"]