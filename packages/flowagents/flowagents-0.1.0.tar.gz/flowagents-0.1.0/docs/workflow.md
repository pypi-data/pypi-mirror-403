# Workflow Engine

Define multi-agent workflows with sequential, parallel, or conditional execution.

## Quick Start

### Define a Workflow (YAML)

```yaml
# workflows/expense.yaml
name: expense_reimbursement
description: Process expense reimbursements

steps:
  - name: collect
    agent: CollectExpenseAgent

  - name: validate
    agent: ValidateExpenseAgent
    inputs:
      expense_data: ${collect.expense_data}

  - name: notify
    agent: NotifyAgent
    inputs:
      result: ${validate.validation_result}
```

### Execute

```python
from flowagent import WorkflowExecutor

executor = WorkflowExecutor(llm_client=my_llm_client)
result = await executor.run("workflows/expense.yaml")
```

## Execution Modes

### Sequential (Default)

```yaml
steps:
  - name: step1
    agent: AgentA

  - name: step2
    agent: AgentB
    inputs:
      data: ${step1.output}
```

### Parallel

```yaml
steps:
  - name: search_flights
    agent: FlightAgent
    parallel_group: search

  - name: search_hotels
    agent: HotelAgent
    parallel_group: search  # Runs in parallel

  - name: combine
    agent: CombineAgent
    depends_on: [search_flights, search_hotels]
```

### Conditional

```yaml
steps:
  - name: check_amount
    agent: CheckerAgent

  - name: auto_approve
    agent: AutoApproveAgent
    condition: ${check_amount.amount} < 100

  - name: manager_approve
    agent: ManagerApproveAgent
    condition: ${check_amount.amount} >= 100
```

## Variable Resolution

```yaml
inputs:
  query: ${query}                    # From executor inputs
  result: ${step_name.output}        # From previous step
  nested: ${step_name.data.field}    # Nested access
  env_var: ${env:API_KEY}            # Environment variable
```

## Error Handling

```yaml
steps:
  - name: api_call
    agent: APIAgent
    retry:
      max_attempts: 3
      delay: 1.0
    on_error: continue  # or: stop, fallback
```

## Programmatic Workflow

```python
from flowagent import Workflow, WorkflowStep, WorkflowExecutor

workflow = Workflow(
    name="expense_flow",
    steps=[
        WorkflowStep(name="collect", agent_type="CollectExpenseAgent"),
        WorkflowStep(
            name="validate",
            agent_type="ValidateExpenseAgent",
            inputs={"data": "${collect.expense_data}"}
        ),
    ]
)

executor = WorkflowExecutor(llm_client=client)
result = await executor.run_workflow(workflow)
```

## Best Practices

1. **Keep steps focused** - One step = one action
2. **Use parallel groups** - For independent operations
3. **Add timeouts** - Prevent infinite waits
4. **Handle errors** - Use retry/fallback for resilience
