# TODO

- We need to be able to set a time range like we can for the Grafana displays, i.e. last 5", last 1', last 10', today, yesterday, last month, last year, ...
- The time range, we should be able set for the parameter data retrieval, and for the plot separately.
- After a while, the MUST token might be invalidated and we need to be able to login again and retrieve a new token.
- Can I use 'paginated' to build up a plot in chunks of data points?
- [x] Read the configuration from ~/.config/must-tui/config.json
- The MIB file 'pcf.dat' is specific for the PLATO project. Provide the possibility to use a different MIB.

# What I found out

- Pagination works as expected, you provide a limit per page and you feed the cursor into the next request. When the cursor is None, you stop. In the code that I have in `must.py`, there is also a maximum number of pages.


# Questions

