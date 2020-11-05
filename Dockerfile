# References
# :- https://github.com/puckel/docker-airflow

FROM python:3.7-slim-buster
LABEL maintainer="eduardo.trevisani"

# Linux
# Never prompt the user for choices on installation/configuration of packages
ARG DEBIAN_FRONTEND=noninteractive
ENV TERM linux 

# Airflow
ARG AIRFLOW_VERSION=1.10.9
ARG AIRFLOW_USER_HOME=/usr/local/airflow
ARG AIRFLOW_DEPS=""
ENV AIRFLOW_HOME=${AIRFLOW_USER_HOME}
ENV AIRFLOW_GPL_UNIDECODE=yes

USER root

COPY ./entrypoint.sh /

RUN set -e \
    && temp_dependencies=' \
        libkrb5-dev \
        libsasl2-dev \
        libssl-dev \
        libffi-dev \
        libpq-dev \
        git \
    ' \
    && apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
        apt-utils \
        build-essential \
        default-libmysqlclient-dev \
        curl \
        rsync \
        netcat \
        locales \
        python3-pip \
        python3-dev \
        python3-psycopg2 \
        libpq-dev \
        libaio1 \
        libaio-dev \
        $temp_dependencies \
    && for i in $(seq 1 8); do mkdir -p "/usr/share/man/man${i}"; done \
    && apt-get install -yqq gnupg libpq5 postgresql-client \
    && sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime \
    && dpkg-reconfigure tzdata \
    && useradd -ms /bin/bash -d ${AIRFLOW_USER_HOME} airflow \
    && chown -R airflow: ${AIRFLOW_USER_HOME} \
    && chown airflow:airflow /entrypoint.sh \
    && chmod 700 /entrypoint.sh \
    && pip install -qqU pip setuptools wheel \
    && pip install -q pytz \
    && pip install -q pyOpenSSL \
    && pip install -q ndg-httpsclient \
    && pip install -q pyasn1 \
    && pip install -q 'redis==3.2' \
    && pip install -qq apache-airflow[crypto,password,celery,async,hive,jdbc,postgres,ssh${AIRFLOW_DEPS:+,}${AIRFLOW_DEPS}]==${AIRFLOW_VERSION} \
    && apt-get purge --auto-remove -qq $temp_dependencies \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

USER airflow
WORKDIR ${AIRFLOW_USER_HOME}

EXPOSE 8080 5555 8793
ENTRYPOINT ["/entrypoint.sh"]