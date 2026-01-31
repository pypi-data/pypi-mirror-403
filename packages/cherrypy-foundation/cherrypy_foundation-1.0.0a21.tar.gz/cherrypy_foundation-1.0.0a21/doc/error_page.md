# Error Pages

The `error_page` utility replaces CherryPy's default error pages with a more flexible error handler.  
It generates error responses based on the response `Content-Type`, returning either:

- an HTML page (default),
- a JSON error response for `application/json`
- plain text for `text/plain`.

If available, the HTML error page is rendered using Jinja2 with a template named `error_page.html`.

⚠️ **Note:** For 404 errors, the error handler sanitizes the error message to avoid leaking path information. A generic message is returned instead of exposing the requested path.

## Setup

```python
from cherrypy_foundation.error_page import error_page

cherrypy.config.update({
    'error_page.default': error_page,
})
```

## Features

### Content Negotiation

The error handler automatically detects the expected response format:

**HTML Response** (default for browsers):
```http
GET /invalid-page HTTP/1.1
Accept: text/html

HTTP/1.1 404 Not Found
Content-Type: text/html

<!DOCTYPE html>
<html>
  <head><title>404 Not Found</title></head>
  <body>
    <h2>404 Not Found</h2>
    <p>Nothing matches the given URI</p>
  </body>
</html>
```

**JSON Response** (for API clients):
```http
GET /api/invalid HTTP/1.1
Accept: application/json

HTTP/1.1 404 Not Found
Content-Type: application/json

{"message": "Nothing matches the given URI", "status": "404 Not Found"}
```

**Plain Text Response**:
```http
GET /invalid HTTP/1.1
Accept: text/plain

HTTP/1.1 404 Not Found
Content-Type: text/plain

Nothing matches the given URI
```

### Server Error Logging

All internal server error 500 are automatically logged with full traceback information:

```python
@cherrypy.expose
def broken(self):
    raise ValueError("Something went wrong!")
    
# Logs: error page status=500 Internal Server Error message=ValueError: Something went wrong!
#       [full traceback]
```

### Custom Error Pages with Jinja2

To use custom error page templates, create an `error_page.html` template in your Jinja2 environment:

The following variables are available in the `error_page.html` template:

- `status` (str): HTTP status code and message (e.g., "404 Not Found")
- `message` (str): Detailed error message
- `traceback` (str): Stack trace (only for server errors when debug mode is enabled)
- `version` (str): CherryPy version


```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{{ status }}</title>
    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
  </head>
  <body>
    <div class="container mt-5">
      <div class="alert alert-danger">
        <h1>{{ status }}</h1>
        <p>{{ message }}</p>
        
        {% if traceback %}
        <details>
          <summary>Technical Details</summary>
          <pre>{{ traceback }}</pre>
        </details>
        {% endif %}
      </div>
    </div>
  </body>
</html>
```

## Complete Example

```python
import cherrypy
from cherrypy_foundation.error_page import error_page

# Setup Jinja2
env = cherrypy.tools.jinja2.create_env(
    package_name=__package__,
)

# Configure error handler
cherrypy.config.update({
    'error_page.default': error_page,
})

@cherrypy.tools.jinja2(env=env)
class Root:
    
    @cherrypy.expose
    @cherrypy.tools.jinja2(template='index.html')
    def index(self):
        return {}
    
    @cherrypy.expose
    def not_found(self):
        # Will trigger 404 error page
        raise cherrypy.NotFound()
    
    @cherrypy.expose
    def server_error(self):
        # Will trigger 500 error page with logging
        raise ValueError("Database connection failed")
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def api_endpoint(self):
        # API errors will return JSON
        raise cherrypy.HTTPError(400, "Invalid request parameters")

if __name__ == '__main__':
    cherrypy.quickstart(Root())
```
