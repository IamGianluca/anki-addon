The domain model should not have any dependencies with application and infrastructure layers. One rule of thumb to check that is to look at the imports. Make sure you are not importing anything from application and infrastructure layers when working on the domain layer. 

This separation is not arbitrary. Having a domain layer without application and infrastructure dependencies gives us more freedom to test things rapidly, and keeps the logic simple.


#### Imports

You will notice that we use relative imports instead of absolute across the entire add-on codebase, with the exclusion of the test suite. This is needed since Anki will not install the add-on as a library, but instead loads it directly from the add-ons folder, requiring relative imports for proper module resolution

```python
from datetime import datetime

from anki.notes import Note

from ...domain.models.completion_result import CompletionResult
from ...infrastructure.openai import OpenAIClient
```

## Domain-Driven Design

![Architecture Patterns in Python](https://www.cosmicpython.com/)

## Testing

![Testing without Mocks](https://www.jamesshore.com/v2/projects/nullables/testing-without-mocks)

