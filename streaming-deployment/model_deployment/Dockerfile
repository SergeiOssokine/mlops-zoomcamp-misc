FROM public.ecr.aws/lambda/python:3.10

RUN pip install -U pip
RUN pip install uv 

COPY [ "model_deployment/requirements.txt",  "./" ]

RUN uv pip install --system --no-cache -r requirements.txt

COPY [ "model_deployment/lambda_function.py", "./" ]

CMD [ "lambda_function.lambda_handler" ]
