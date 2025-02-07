FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt . 
RUN pip3 install -r requirements.txt --target ${LAMBDA_TASK_ROOT}

COPY cz_telem_shipper.py ${LAMBDA_TASK_ROOT}
COPY download_and_ship.py ${LAMBDA_TASK_ROOT}
COPY lambda.py ${LAMBDA_TASK_ROOT}
COPY unit_csv_to_cz_json.py ${LAMBDA_TASK_ROOT}
COPY converted_cz_json_file.py ${LAMBDA_TASK_ROOT}
COPY ./unit_allocation_csv ${LAMBDA_TASK_ROOT}/unit_allocation_csv

CMD ["lambda.handle"]

