FROM public.ecr.aws/lambda/python:3.10

RUN pip install -U pip
RUN pip install uv 

COPY [ "requirements.txt",  "./" ]

RUN uv pip install --system --no-cache -r requirements.txt

COPY [ "lambda_function.py", "./" ]

CMD [ "lambda_function.lambda_handler" ]
