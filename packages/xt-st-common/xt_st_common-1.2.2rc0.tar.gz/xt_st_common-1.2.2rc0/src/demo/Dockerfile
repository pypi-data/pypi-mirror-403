FROM python:3.10-slim
EXPOSE 8080
ARG PRIVATE_PIP_INDEX_URL

# If the requirements include a git repo you need to include git in the image..
# NOTE: Git is quite large compared to the python:3.10-slim image so only install if required!
RUN apt-get update \
  && apt-get install -y --no-install-recommends git \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./requirements.txt
COPY run.py ./run.py
RUN pip install --extra-index-url=${PRIVATE_PIP_INDEX_URL} -r requirements.txt
COPY .streamlit/prod-config.toml /app/.streamlit/config.toml
ADD static /app/static
ADD mpl_toolbox_ui /app/mpl_toolbox_ui
RUN python -c 'import run; run.update_static_files()'
CMD streamlit run run.py --server.port 8080
