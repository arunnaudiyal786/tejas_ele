# CrewAI Flow Implementation

This directory contains a CrewAI Flow implementation for query termination management using the Flow class with `@start` and `@listen` decorators.

## Overview

The `QueryTerminationFlow` class orchestrates the query termination process using CrewAI's Flow system. It provides a structured way to:

1. **Initialize** the flow with input parameters
2. **Validate** inputs and determine processing approach
3. **Execute** the query termination using the existing CrewAI crew
4. **Finalize** the flow and update status

## Key Components

### 1. QueryTerminationState
A Pydantic model that manages the state throughout the flow execution:
- `ticket_id`: Optional ticket ID to process
- `process_id`: Optional process ID to process  
- `query_id`: Optional query ID to process
- `identifier_type`: Type of identifier being used
- `termination_result`: Results from the crew execution
- `final_status`: Final status of the flow

### 2. QueryTerminationFlow
The main flow class that inherits from `Flow[QueryTerminationState]`:

#### Flow Steps:
- **`@start()`**: `initialize_flow()` - Initializes the flow with parameters
- **`@listen(initialize_flow)`**: `validate_inputs()` - Validates and determines processing approach
- **`@listen(validate_inputs)`**: `execute_query_termination()` - Executes the CrewAI crew
- **`@listen(execute_query_termination)`**: `finalize_flow()` - Finalizes and updates status

## Usage

### Basic Usage

```python
from flow import kickoff_flow

# Process by ticket ID
result = kickoff_flow(ticket_id=1)

# Process by process ID
result = kickoff_flow(process_id=12345)

# Process by query ID
result = kickoff_flow(query_id=67890)
```

### Advanced Usage

```python
from flow import create_query_termination_flow

# Create a custom flow instance
flow = create_query_termination_flow(ticket_id=999)

# Inspect state before execution
print(f"Ticket ID: {flow.state.ticket_id}")
print(f"Identifier Type: {flow.state.identifier_type}")

# Execute the flow
result = flow.kickoff()

# Check final state
print(f"Final Status: {flow.state.final_status}")
print(f"Termination Result: {flow.state.termination_result}")
```

### Flow State Management

The flow automatically manages state throughout execution:

```python
# State is automatically updated at each step
flow = create_query_termination_flow(ticket_id=1)

# Before execution
print(flow.state.final_status)  # "pending"

# After execution
result = flow.kickoff()
print(flow.state.final_status)  # "completed" or "failed"
print(flow.state.termination_result)  # Results from crew execution
```

## Flow Visualization

Generate a visual representation of the flow:

```python
from flow import plot_flow

# Generate flow plot
plot_flow()
```

This creates a file called `QueryTerminationFlowPlot` showing the flow structure.

## Error Handling

The flow includes comprehensive error handling:

```python
try:
    result = kickoff_flow(ticket_id=1)
    if result['success']:
        print("Flow completed successfully")
    else:
        print(f"Flow failed: {result['error']}")
except Exception as e:
    print(f"Exception occurred: {e}")
```

## Integration with Existing Crew

The flow seamlessly integrates with your existing `QueryTerminationCrew`:

1. **Initialization**: Flow sets up the crew instance
2. **Execution**: Flow calls the crew's `kickoff()` method
3. **Results**: Flow captures and stores crew results in state
4. **Status**: Flow tracks the overall execution status

## Testing

Run the test suite to verify flow functionality:

```bash
cd backend
python test_flow.py
```

Run examples to see practical usage:

```bash
cd backend
python example_flow_usage.py
```

## Flow Execution Order

The flow executes in this sequence:

1. **Start**: `initialize_flow()` - Sets up initial parameters
2. **Validation**: `validate_inputs()` - Validates and determines approach
3. **Execution**: `execute_query_termination()` - Runs the CrewAI crew
4. **Finalization**: `finalize_flow()` - Updates final status

Each step listens to the completion of the previous step using the `@listen` decorator.

## Benefits of Using Flow

1. **Structured Execution**: Clear step-by-step process flow
2. **State Management**: Automatic state tracking throughout execution
3. **Error Handling**: Built-in error handling and status tracking
4. **Visualization**: Generate flow diagrams for documentation
5. **Integration**: Seamlessly works with existing CrewAI crews
6. **Flexibility**: Easy to modify flow steps and add new functionality

## Customization

To add new flow steps:

```python
@listen(execute_query_termination)
def new_step(self):
    """New custom step."""
    # Your logic here
    return "Step completed"

@listen(new_step)
def finalize_flow(self):
    # Updated finalization
    pass
```

## Dependencies

Ensure you have the required dependencies:

```bash
pip install crewai>=0.28.8
pip install pydantic>=2.0.0
```

The flow system is built on top of CrewAI's Flow class and integrates with your existing agent infrastructure.
