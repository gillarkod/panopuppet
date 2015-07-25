# PanoPuppet API
PanoPuppet pages uses a series of ajax requests to the PanoPuppet API that generate and populate the data into
the pages tables and graphs.

Most of these API's require authentication and the need for you to be authenticated before it is possible to use them.

# Open API Endpoints
These are the endpoints that don't require authentication to call. They don't leak sensitive data or specific changes
or nodes.

## /pano/api/status
JSON Response containing total number of nodes, changed, unchanged, noop, and failing.
Suitable for scripting if you want some kind of monitoring to check if more than x % of total nodes are failing.

### Input parameters
* GET request
* Takes no input parameters.
