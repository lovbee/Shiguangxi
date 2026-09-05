# FROM 指定使用哪个镜像作为基准
FROM openjdk:17-jdk-alpine

# 创建目录, 并设置该目录为工作目录
RUN mkdir -p /xiaohashu
WORKDIR /xiaohashu

# 复制文件到镜像中
COPY target/xiaohashu-search-biz-0.0.1-SNAPSHOT.jar app.jar

# 设置时区
ENV TZ=Asia/Shanghai

# 设置 JAVA_OPTS 环境变量，可通过 docker run -e "JAVA_OPTS=" 进行覆盖
ENV JAVA_OPTS="-Xms200m -Xmx200m -Djava.security.egd=file:/dev/./urandom"

# 应用参数，可通过 docker run -e "ARGS=" 来设置，如 -e "ARGS=--spring.profiles.active=prod"
ENV ARGS=""

# 暴露 8080 端口
EXPOSE 8092

# 启动后端服务
CMD java ${JAVA_OPTS} -jar app.jar $ARGS
