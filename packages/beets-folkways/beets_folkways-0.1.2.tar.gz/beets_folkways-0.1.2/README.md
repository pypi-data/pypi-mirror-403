[Folkways](https://folkways.si.edu/) autotagger plugin for [beets](https://beets.io/).

It directly scrapes the html of the website which makes it prone to breakage.
The meta tags are sadly even more inconsistent than the info boxes, so for now, that's what this code is using.

As I only test it with the folkways records I actually own, the rest of their catalogue might have still other ways storing
their values that this library is not aware of.
