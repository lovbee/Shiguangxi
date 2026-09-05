FROM openjdk:17-jdk-alpine

RUN mkdir -p /xiaohashu
WORKDIR /xiaohashu

COPY target/xiaohashu-voice-agent-biz-0.0.1-SNAPSHOT.jar app.jar

ENV TZ=Asia/Shanghai
ENV JAVA_OPTS="-Xms200m -Xmx200m -Djava.security.egd=file:/dev/./urandom"
ENV ARGS=""

EXPOSE 8094

CMD java ${JAVA_OPTS} -jar app.jar $ARGS
