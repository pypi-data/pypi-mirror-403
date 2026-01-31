# URL Generation

The `url_for` utility provides a flexible way to generate URLs in your CherryPy application.  
It handles path construction, query parameters, and supports multiple URL formats (absolute, relative, server-relative).

## Setup

### 1. Enable `url_for` in Jinja2 templates

```python
import cherrypy
from cherrypy_foundation.url import url_for

# Create Jinja2 environment with url_for available
env = cherrypy.tools.jinja2.create_env(
    package_name=__package__,
    globals={'url_for': url_for},
)

@cherrypy.tools.jinja2(env=env)
class Root:

    @cherrypy.expose
    @cherrypy.tools.jinja2(template='index.html')
    def index(self, **kwargs):
        return {}

```

## Usage

### Simple path construction

```python
from cherrypy_foundation import url_for

# Simple path
url_for('/users')
# => '/users'

# Path with segments
url_for('/users', 123, 'edit')
# => '/users/123/edit'

# Path with query parameters
url_for('/search', q='python', page=2)
# => '/search?q=python&page=2'
```

### Path Construction

The function accepts multiple positional arguments that are joined to form the path:

**Simple strings:**

```python
# String segments (leading/trailing slashes are handled automatically)
url_for('users', 'profile')
# => '/users/profile'

url_for('/users/', '/profile/')
# => '/users/profile'
```

**Integers and basic objects get cast into strings:**

```python
# Integer segments
user_id = 42
url_for('/users', user_id)
# => '/users/42'

# Mixed types
url_for('/api', 'v1', 'users', 123, 'posts')
# => '/api/v1/users/123/posts'
```

**Customize object URL representation with `__url_for__()` method:**

```python
# Objects with __url_for__() method
class User:
    def __init__(self, id):
        self.id = id

    def __url_for__(self):
        return f'users/{self.id}'

user = User(123)
url_for(user, 'edit')
# => '/users/123/edit'
```

**Or define a `url_for` property:**

```python
# Objects with url_for attribute
class Article:
    def __init__(self, slug):
        self.url_for = f'articles/{slug}'

article = Article('hello-world')
url_for(article)
# => '/articles/hello-world'

url_for(article, 'comments')
# => '/articles/hello-world/comments'
```

### URL Formats

Use the `_relative` parameter to control the URL format:

```python
# Default: CherryPy default behavior (usually server-relative)
url_for('/users')
# => '/users'

# Absolute URL (includes scheme and host)
url_for('/users', _relative=False)
# => 'https://example.com/users'

# Relative to current path
url_for('..', 'admin', _relative=True)
# => '../admin'

# Server-relative (starts with '/')
url_for('/api', 'users', _relative='server')
# => '/api/users'
```

### Query Parameters

Pass query parameters as keyword arguments:

```python
url_for('/search', q='cherrypy', category='web', page=1)
# => '/search?category=web&page=1&q=cherrypy'

# None values are automatically filtered out
url_for('/search', q='test', filter=None)
# => '/search?q=test'
```

### Special Behavior: Empty Path

When no path arguments are provided, `url_for` preserves the current request's path and merges query parameters:

```python
# Current URL: /search?q=python&page=1

# Update only the page parameter
url_for(page=2)
# => '/search?page=2&q=python'

# Add a new parameter
url_for(sort='date')
# => '/search?page=1&q=python&sort=date'
```

### Base URL Override

Use `_base` to specify a custom base URL:

```python
url_for('/api', 'users', _base='https://api.example.com')
# => 'https://api.example.com/api/users'
```

⚠️ **Note:** When called outside a request context, `url_for` will use the `tools.proxy.base` configuration if available.

### In Jinja2 Templates

The `url_for` function is not automatically available in Jinja2 templates. You need to make it available using:

```python
import cherrypy_foundation.tools.jinja2

env = cherrypy.tools.jinja2.create_env(
    package_name=__package__,
    globals={
        'url_for': url_for,
    },
)
```

In you Jinja template:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Navigation</title>
  </head>
  <body>
    <nav>
      <a href="{{ url_for('/') }}">Home</a>
      <a href="{{ url_for('/users') }}">Users</a>
      <a href="{{ url_for('/users', user.id) }}">Profile</a>
      <a href="{{ url_for('/search', q='python') }}">Search</a>
    </nav>
  </body>
</html>
```

## Complete Example

```python
import cherrypy
from cherrypy_foundation import url_for

class Root:
    
    @cherrypy.expose
    def index(self):
        # Redirect to user profile
        user_id = 123
        raise cherrypy.HTTPRedirect(url_for('/users', user_id))
    
    @cherrypy.expose
    @cherrypy.tools.jinja2(template='users.html')
    def users(self, user_id):
        # Generate URLs for template
        edit_url = url_for('/users', user_id, 'edit')
        delete_url = url_for('/users', user_id, 'delete')
        return {
            'edit_url': edit_url,
            'delete_url': delete_url
        }
```
