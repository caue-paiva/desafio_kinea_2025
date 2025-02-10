FROM mambaorg/micromamba:0.15.3
USER root
RUN apt-get update && DEBIAN_FRONTEND=“noninteractive”
RUN mkdir /opt/appdashboardkinea
RUN chmod -R 777 /opt/appdashboardkinea
WORKDIR /opt/appdashboardkinea
USER micromamba
COPY environment.yml environment.yml
RUN micromamba install -y -n base -f environment.yml && \
    micromamba clean --all --yes
COPY run.sh run.sh
COPY Projeto Projeto
USER root
RUN chmod a+x run.sh
CMD ["./run.sh"]