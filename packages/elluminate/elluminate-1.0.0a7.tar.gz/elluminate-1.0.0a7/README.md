# elluminate SDK

elluminate SDK is a Software Development Kit that provides a convenient way to interact with the elluminate platform programmatically. It enables developers to evaluate and optimize prompts, manage experiments, and integrate elluminate's powerful evaluation capabilities directly into their applications.

## Installation

Install the elluminate SDK using pip:

```bash
pip install elluminate
```

## 📚 Full Documentation

The full documentation of elluminate including the SDK can be found at: <https://docs.elluminate.de/>

## Quick Start

### Prerequisites

Before you begin, you'll need to set up your API key:

1. Visit your project's "Keys" dashboard to create a new API key
2. Export your API key and service address as environment variables:

```bash
export ELLUMINATE_API_KEY=<your_api_key>
export ELLUMINATE_BASE_URL=<your_elluminate_service_address>
```

Never commit your API key to version control. For detailed information about API key management and security best practices, see our [API Key Management Guide](https://docs.elluminate.de/get_started/api_keys/).

### Basic Usage

Here's a simple example to evaluate your first prompt:

```python
from elluminate import Client

# Initialize the client
client = Client()

# Create a prompt template
template, _ = client.get_or_create_prompt_template(
    name="Concept Explanation",
    messages=[{"role": "user", "content": "Explain the concept of {{concept}} in simple terms."}],
)

# Generate evaluation criteria for the template
template.get_or_generate_criteria()

# Create a collection with test cases
collection, _ = client.get_or_create_collection(
    name="Concept Variables",
    defaults={
        "description": "Template variables for concept explanations",
        "variables": [{"concept": "recursion"}],
    },
)

# Run a complete experiment (generates responses + rates them)
experiment = client.run_experiment(
    name="Concept Evaluation Test",
    prompt_template=template,
    collection=collection,
    description="Evaluating concept explanation responses",
)

# Print results
for response in experiment.responses():
    print(f"Response: {response.response_str}")
    for rating in response.ratings:
        print(f"  Criterion: {rating.criterion.criterion_str}")
        print(f"  Rating: {rating.rating}")
```

### Alternative Client Initialization

You can also initialize the client by directly passing the API key and/or base url:

```python
client = Client(api_key="your-api-key", base_url="your-base-url")
```

## Advanced Features

### Batch Evaluation with Experiments

For evaluating prompts across multiple test cases:

```python
from elluminate import Client
from elluminate.schemas import RatingMode

client = Client()

# Create a prompt template
template, _ = client.get_or_create_prompt_template(
    name="Math Teaching Prompt",
    messages=[{"role": "user", "content": "Explain {{math_concept}} to a {{grade_level}} student using simple examples."}],
)

# Generate evaluation criteria
template.get_or_generate_criteria()

# Create a collection with multiple test cases
collection, _ = client.get_or_create_collection(
    name="Math Teaching Test Cases",
    defaults={"description": "Various math concepts and grade levels"},
)

# Add test cases in batch
collection.add_many(
    variables=[
        {"math_concept": "fractions", "grade_level": "5th grade"},
        {"math_concept": "algebra", "grade_level": "8th grade"},
        {"math_concept": "geometry", "grade_level": "6th grade"},
    ]
)

# Run the experiment (handles all response generation and rating)
experiment = client.run_experiment(
    name="Math Teaching Evaluation",
    prompt_template=template,
    collection=collection,
    description="Evaluating math explanations across different concepts and grade levels",
    rating_mode=RatingMode.DETAILED,  # Get reasoning with ratings
)

# Print results for each response
for response in experiment.responses():
    variables = response.prompt.template_variables.input_values
    print(f"\nConcept: {variables['math_concept']}, Grade: {variables['grade_level']}")
    print(f"Response: {response.response_str[:100]}...")

    for rating in response.ratings:
        print(f"  • {rating.criterion.criterion_str}: {rating.rating}")
        if rating.reasoning:
            print(f"    Reasoning: {rating.reasoning}")
```

### Evaluating External Agents

To evaluate responses from external systems (LangChain agents, OpenAI Assistants, custom APIs):

```python
from elluminate import Client
from elluminate.schemas import RatingValue

client = Client()

# Set up template and collection
template, _ = client.get_or_create_prompt_template(
    name="Agent Evaluation",
    messages=[{"role": "user", "content": "Answer: {{question}}"}],
)
template.get_or_generate_criteria()

collection, _ = client.get_or_create_collection(
    name="Agent Test Cases",
    defaults={"variables": [{"question": "What is Python?"}]},
)

# Create experiment WITHOUT auto-generation
experiment = client.create_experiment(
    name="External Agent Eval",
    prompt_template=template,
    collection=collection,
)

# Get responses from your external agent
external_responses = ["Python is a high-level programming language..."]
template_vars = list(collection.items())

# Upload responses and rate them
experiment.add_responses(responses=external_responses, template_variables=template_vars)
experiment.rate_responses()

# Analyze results
for response in experiment.responses():
    passed = sum(1 for r in response.ratings if r.rating == RatingValue.YES)
    print(f"Pass rate: {passed}/{len(response.ratings)}")
```

## Additional Resources

- [General Documentation](https://docs.elluminate.de/)
- [Key Concepts Guide](https://docs.elluminate.de/guides/the_basics/)
- [API Documentation](https://docs.elluminate.de/elluminate/client/)
