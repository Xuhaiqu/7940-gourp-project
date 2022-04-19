FROM python:3.9
COPY requirements.txt /
COPY chatbot.py /
COPY config.ini /
RUN pip install update
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt
CMD python chatbot.py