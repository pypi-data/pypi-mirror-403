FROM python:3.11

# Install dependencies
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get install -y r-base perl
RUN pip install --root-user-action=ignore --upgrade pip
# clean up to reduce size
RUN apt-get -y clean
RUN apt-get -y autoremove
RUN apt-get -y autoclean
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /home
ADD . /home/

# get all python dependencies
RUN pip install --root-user-action=ignore -e .[test]

# install isocorrector
RUN python -c 'from unac.prep import install_isocorrector; install_isocorrector()'
