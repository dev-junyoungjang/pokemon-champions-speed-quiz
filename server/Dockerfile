FROM public.ecr.aws/lambda/python:3.13

# Install deps into the Lambda task root.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code + curated data (held items / species local fallback) at the task root.
COPY . ${LAMBDA_TASK_ROOT}

# FastAPI app wrapped by Mangum (app/main.py: handler = Mangum(app)).
CMD ["app.main.handler"]
