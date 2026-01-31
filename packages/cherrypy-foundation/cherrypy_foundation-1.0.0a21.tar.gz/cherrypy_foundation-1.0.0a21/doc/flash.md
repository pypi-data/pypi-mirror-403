# Flash Messages

Flash messages are used to display informational, warning, or error messages to the user.  
They are especially useful for reporting success or validation errors after form submissions.

⚠️ **Important:** Flash messages require the CherryPy **sessions tool** to be enabled, as messages are stored in the user session.

## How It Works

1. **Storage**: Flash messages are stored in the user's session under the `flash` key
2. **Retrieval**: `get_flashed_messages()` retrieves all messages and clears them from the session
3. **One-time display**: Messages are automatically removed after being retrieved, ensuring they only display once

This makes flash messages perfect for post-redirect-get patterns where you want to show a message after a form submission.

## Setup

### 1. Enable Sessions and Configure Jinja2

```python
import cherrypy
from cherrypy_foundation.flash import get_flashed_messages

# Create Jinja2 environment with get_flashed_messages available
env = cherrypy.tools.jinja2.create_env(
    package_name=__package__,
    globals={'get_flashed_messages': get_flashed_messages},
)

@cherrypy.tools.sessions(locking='explicit')  # Required for flash messages
@cherrypy.tools.jinja2(env=env)
class Root:
    pass
```

### 2. Display Messages in Templates

Call `get_flashed_messages()` in your Jinja2 template to retrieve and display flash messages:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>My Page</title>
    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
  </head>
  <body>
    <!-- Display flash messages -->
    {% for message in get_flashed_messages() %}
      <div class="alert alert-{{ message.level }} alert-dismissible fade show">
        {{ message.message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    {% endfor %}
    
    <!-- Page content -->
    <h1>Welcome!</h1>
  </body>
</html>
```

## Usage

### Adding Flash Messages

Use the `flash()` function to add messages in your handler:

```python
from cherrypy_foundation.flash import flash

@cherrypy.expose
def save_profile(self, **kwargs):
    # Save user profile...
    flash('Profile updated successfully!', level='success')
    raise cherrypy.HTTPRedirect('/profile')
```

### Message Levels

Flash messages support four severity levels:

- `info` - Informational messages (default)
- `success` - Success confirmations
- `warning` - Warning messages
- `error` - Error messages

```python
flash('Account created successfully', level='success')
flash('Please verify your email address', level='info')
flash('Your session will expire in 5 minutes', level='warning')
flash('Failed to save changes', level='error')
```

### HTML Markup Support

Flash messages support both plain strings and HTML markup:

```python
from markupsafe import Markup

# Plain text
flash('Simple message', level='info')

# HTML markup (safe HTML)
flash(Markup('Click <a href="/help">here</a> for help'), level='info')
```

### Using the JinjaX Flash Component

If you have JinjaX installed, you can use the built-in `<Flash />` component for easier rendering:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>My Page</title>
  </head>
  <body>
    <Flash
      messages="{{ get_flashed_messages() }}"
      class="mb-2"
      style="min-height: 100px"
    />
    
    <h1>Welcome!</h1>
  </body>
</html>
```

The `<Flash />` component automatically handles:
- Rendering messages with appropriate Bootstrap alert classes
- Dismiss buttons for each message
- Custom styling via `class` and `style` attributes

## Complete Example

```python
import cherrypy
import cherrypy_foundation.tools.jinja2
from cherrypy_foundation.flash import flash, get_flashed_messages

# Setup Jinja2
env = cherrypy.tools.jinja2.create_env(
    package_name=__package__,
    globals={'get_flashed_messages': get_flashed_messages},
)

@cherrypy.tools.sessions(locking='explicit')
@cherrypy.tools.jinja2(env=env)
class Root:
    
    @cherrypy.expose
    @cherrypy.tools.jinja2(template='index.html')
    def index(self):
        return {}
    
    @cherrypy.expose
    def submit(self, name=None):
        if not name:
            flash('Name is required', level='error')
        else:
            flash(f'Welcome, {name}!', level='success')
        
        raise cherrypy.HTTPRedirect('/')

if __name__ == '__main__':
    cherrypy.quickstart(Root())
```

**Template: `form.html`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Registration Form</title>
    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
  </head>
  <body>
    <div class="container mt-5">
      <!-- Flash messages -->
      {% for message in get_flashed_messages() %}
        <div class="alert alert-{{ message.level }} alert-dismissible">
          {{ message.message }}
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      {% endfor %}
      
      <!-- Form -->
      <form method="post" action="/submit">
        <div class="mb-3">
          <label for="name" class="form-label">Name</label>
          <input type="text" class="form-control" id="name" name="name">
        </div>
        <button type="submit" class="btn btn-primary">Submit</button>
      </form>
    </div>
  </body>
</html>
```
