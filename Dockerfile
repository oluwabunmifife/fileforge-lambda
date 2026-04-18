FROM public.ecr.aws/lambda/python:3.12

RUN dnf install -y libheif libde265 \
    && dnf clean all \
    && rm -rf /var/cache/dnf

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

COPY . ${LAMBDA_TASK_ROOT}

CMD ["lambda_function.lambda_handler"]
