# Cron

Types:

```python
from rocktick.types import CronJob, HTTPRequest, CronListResponse
```

Methods:

- <code title="post /api/cron">client.cron.<a href="./src/rocktick/resources/cron.py">create</a>(\*\*<a href="src/rocktick/types/cron_create_params.py">params</a>) -> <a href="./src/rocktick/types/cron_job.py">CronJob</a></code>
- <code title="get /api/cron/{job_id}">client.cron.<a href="./src/rocktick/resources/cron.py">retrieve</a>(job_id) -> <a href="./src/rocktick/types/cron_job.py">CronJob</a></code>
- <code title="post /api/cron/{job_id}">client.cron.<a href="./src/rocktick/resources/cron.py">update</a>(job_id, \*\*<a href="src/rocktick/types/cron_update_params.py">params</a>) -> <a href="./src/rocktick/types/cron_job.py">CronJob</a></code>
- <code title="get /api/cron">client.cron.<a href="./src/rocktick/resources/cron.py">list</a>(\*\*<a href="src/rocktick/types/cron_list_params.py">params</a>) -> <a href="./src/rocktick/types/cron_list_response.py">SyncCursorPage[CronListResponse]</a></code>

# Executions

Types:

```python
from rocktick.types import Execution, HTTPResponse, ExecutionListResponse
```

Methods:

- <code title="get /api/executions/{execution_id}">client.executions.<a href="./src/rocktick/resources/executions.py">retrieve</a>(execution_id) -> <a href="./src/rocktick/types/execution.py">Execution</a></code>
- <code title="get /api/executions">client.executions.<a href="./src/rocktick/resources/executions.py">list</a>(\*\*<a href="src/rocktick/types/execution_list_params.py">params</a>) -> <a href="./src/rocktick/types/execution_list_response.py">SyncCursorPage[ExecutionListResponse]</a></code>

# Jobs

Types:

```python
from rocktick.types import OneOffJob, JobListResponse
```

Methods:

- <code title="post /api/jobs">client.jobs.<a href="./src/rocktick/resources/jobs.py">create</a>(\*\*<a href="src/rocktick/types/job_create_params.py">params</a>) -> <a href="./src/rocktick/types/one_off_job.py">OneOffJob</a></code>
- <code title="get /api/jobs/{job_id}">client.jobs.<a href="./src/rocktick/resources/jobs.py">retrieve</a>(job_id) -> <a href="./src/rocktick/types/one_off_job.py">OneOffJob</a></code>
- <code title="post /api/jobs/{job_id}">client.jobs.<a href="./src/rocktick/resources/jobs.py">update</a>(job_id, \*\*<a href="src/rocktick/types/job_update_params.py">params</a>) -> <a href="./src/rocktick/types/one_off_job.py">OneOffJob</a></code>
- <code title="get /api/jobs">client.jobs.<a href="./src/rocktick/resources/jobs.py">list</a>(\*\*<a href="src/rocktick/types/job_list_params.py">params</a>) -> <a href="./src/rocktick/types/job_list_response.py">SyncCursorPage[JobListResponse]</a></code>

# Tenants

Types:

```python
from rocktick.types import Tenant
```

Methods:

- <code title="post /api/tenants">client.tenants.<a href="./src/rocktick/resources/tenants.py">create</a>(\*\*<a href="src/rocktick/types/tenant_create_params.py">params</a>) -> <a href="./src/rocktick/types/tenant.py">Tenant</a></code>
- <code title="get /api/tenants/{tenant_id}">client.tenants.<a href="./src/rocktick/resources/tenants.py">retrieve</a>(tenant_id) -> <a href="./src/rocktick/types/tenant.py">Tenant</a></code>
- <code title="post /api/tenants/{tenant_id}">client.tenants.<a href="./src/rocktick/resources/tenants.py">update</a>(tenant_id, \*\*<a href="src/rocktick/types/tenant_update_params.py">params</a>) -> <a href="./src/rocktick/types/tenant.py">Tenant</a></code>

# Verify

Types:

```python
from rocktick.types import VerifyRetrieveResponse
```

Methods:

- <code title="get /api/verify/{job_id}">client.verify.<a href="./src/rocktick/resources/verify.py">retrieve</a>(job_id) -> <a href="./src/rocktick/types/verify_retrieve_response.py">VerifyRetrieveResponse</a></code>
