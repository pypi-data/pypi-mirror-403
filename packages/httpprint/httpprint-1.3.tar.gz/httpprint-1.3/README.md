# httpprint

This module changes python's builtin print method to one that hosts a terminal clone on a flask server.
It needs almost no changes to the code, so it can be integrated easily into your projects.

## Usage

Just add

```
from httpprint import print
```

into the import section of every file that prints.

...and you're done! When you run the code, a http server is opened on port 5580. Everything you print to the console also gets shown here. Update the page to view new changes.

## Currently supported terminal behaviours

- `\t` pads to the next multiple of **8** spaces
- `\n` for newlines
- Filtered output: `<` and `>` don't break the entire page

## Planned

- Escape sequences for coloring
