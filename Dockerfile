FROM public.ecr.aws/lambda/python:3.12

ENV DATA_DIR=/tmp/data

RUN dnf install -y \
    atk \
    cups-libs \
    gtk3 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXrandr \
    libXScrnSaver \
    libXtst \
    pango \
    alsa-lib \
    liberation-fonts \
    vulkan-loader \
    xdg-utils \
    wget \
    unzip \
    && dnf clean all \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm \
    && rpm -Uvh google-chrome-stable_current_x86_64.rpm \
    && rm google-chrome-stable_current_x86_64.rpm \
    && CHROME_VERSION=$(google-chrome-stable --version | awk '{print $3}') \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip -q chromedriver-linux64.zip -d /opt \
    && mv /opt/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf chromedriver-linux64.zip /opt/chromedriver-linux64

COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY src ${LAMBDA_TASK_ROOT}/src
COPY handlers ${LAMBDA_TASK_ROOT}/handlers

CMD ["handlers.crawling_handler.lambda_handler"]