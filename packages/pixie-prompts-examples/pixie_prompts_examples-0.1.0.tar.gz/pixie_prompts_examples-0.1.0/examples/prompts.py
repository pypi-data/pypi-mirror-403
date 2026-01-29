from pixie.prompts import Variables, create_prompt


simple_prompt = create_prompt(
    "simple_prompt", description="A simple prompt with no variables."
)


class Person(Variables):
    name: str
    age: int


typed_prompt = create_prompt(
    "typed_prompt",
    Person,
    description="A typed prompt with specific variables.",
)


class Contact(Variables):
    email: str
    phone: str
    person: Person


nested_typed_prompt = create_prompt(
    "nested_typed_prompt",
    Contact,
    description="A typed prompt with nested variable structures.",
)


class Resume(Variables):
    full_name: str
    last_employer: str | None
    skills: list[str]


complex_prompt = create_prompt(
    "complex_prompt",
    Resume,
    description="A complex prompt with lists and optional fields.",
)
