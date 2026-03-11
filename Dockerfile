FROM public.ecr.aws/lambda/python:3.12

RUN dnf install -y libheif

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["lambda_function.lambda_handler"]