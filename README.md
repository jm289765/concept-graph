concept-graph is the server used by [concept-graph-web](https://github.com/jm289765/concept-graph-web).

This server should only be hosted and accessed locally. I plan to eventually use it for remote access, but until then, I have no reason to implement any security measures. Current security problems include using HTTP instead of HTTPS and having no user authentication for PUT and PATCH requests.

Uses a [Redis](https://redis.io/) database and [Apache Solr](https://solr.apache.org/) as a search engine.
