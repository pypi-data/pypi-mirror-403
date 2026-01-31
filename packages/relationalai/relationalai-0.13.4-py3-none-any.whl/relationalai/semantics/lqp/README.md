# Logic Engine LQP Backend

The logic engine runs the *Logical Query Protocol* (short *LQP*). This module includes a
compiler from the semantic metamodel to LQP along with an executor.

## Running against a local logic engine

For development and testing, it is possible to run PyRel models against a local logic engine
server process.

To start your local server, please refer to the [logic engine
docs](https://github.com/RelationalAI/raicode/tree/master/src/Server#starting-the-server).

With the local server running, add this to your `raiconfig.toml`:

```toml
[profile.local]
platform = "local"
engine = "local"
host = "localhost"
port = 8010
```

Then set `active_profile = "local"` at the top of the file.

**Known limitations:**

Local execution does not support running against Snowflake source tables.

At the moment, locally created databases cannot be cleaned up by the client. Eventually you
will need to clear your local pager directory.

At the moment, local execution is only supported for fast-path transactions, i.e. those
which complete in less than 5 seconds. Polling support will be added soon.