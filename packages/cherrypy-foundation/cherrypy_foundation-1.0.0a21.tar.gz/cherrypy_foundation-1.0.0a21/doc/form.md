# Form Handling

The `CherryForm` class extends WTForms to seamlessly integrate with CherryPy, providing automatic form data handling, validation, and rendering capabilities with Jinja2 and JinjaX.

## Features

- **Automatic form data binding** from `cherrypy.request.params` or `cherrypy.request.json`
- **Built-in validation** with `validate_on_submit()`
- **Bootstrap-compatible rendering** with JinjaX components
- **JSON API support** for modern web applications

## How It Works

1. **Automatic Data Binding**: When a form is instantiated, `CherryForm` automatically binds data from `cherrypy.request.params` for POST requests
2. **Validation**: The `validate_on_submit()` method checks if the request is POST and validates all fields
3. **Error Display**: Validation errors are automatically available in the template through `form.field.errors`
4. **JinjaX Integration**: The `<Fields />` and `<Field />` components render Bootstrap-compatible HTML with proper styling and error messages

This approach follows the Post-Redirect-Get pattern, ensuring a clean user experience after form submission.

## Setup

### 1. Define Your Form

```python
from wtforms.fields import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
from cherrypy_foundation.form import CherryForm

class LoginForm(CherryForm):
    login = StringField(
        'Username',
        validators=[InputRequired(), Length(max=256)],
        render_kw={
            "placeholder": "Enter username",
            "autofocus": "autofocus",
        },
    )
    password = PasswordField(
        'Password',
        validators=[InputRequired(), Length(max=256)],
        render_kw={"placeholder": "Enter password"},
    )
    submit = SubmitField('Login')
```

### 2. Use Form in Handler

```python
import cherrypy
import cherrypy_foundation.tools.jinja2

env = cherrypy.tools.jinja2.create_env(
    package_name=__package__,
)

@cherrypy.tools.sessions()
@cherrypy.tools.jinja2(env=env)
class Root:
    
    @cherrypy.expose
    @cherrypy.tools.jinja2(template='login.html')
    def login(self, **kwargs):
        form = LoginForm()
        if form.validate_on_submit():
            # Form is valid - process login
            username = form.login.data
            password = form.password.data
            # TODO: Validate credentials
            cherrypy.session['user'] = username
            raise cherrypy.HTTPRedirect('/')
        return {'form': form}
```

### 3. Render Form in Template

You can render forms manually or use the built-in JinjaX components for automatic Bootstrap-compatible rendering.

**Manual Rendering:**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Login</title>
    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
  </head>
  <body>
    <div class="container mt-5">
      <form method="post">
        <div class="mb-3">
          {{ form.login.label(class="form-label") }}
          {{ form.login(class="form-control") }}
          {% if form.login.errors %}
            <div class="invalid-feedback d-block">{{ form.login.errors[0] }}</div>
          {% endif %}
        </div>
        
        <div class="mb-3">
          {{ form.password.label(class="form-label") }}
          {{ form.password(class="form-control") }}
          {% if form.password.errors %}
            <div class="invalid-feedback d-block">{{ form.password.errors[0] }}</div>
          {% endif %}
        </div>
        
        {{ form.submit(class="btn btn-primary") }}
      </form>
    </div>
  </body>
</html>
```

**Using JinjaX Components:**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Login</title>
    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
  </head>
  <body>
    <div class="container mt-5">
      <form method="post">
        {# Render all fields automatically #}
        <Fields form="{{ form }}" />
      </form>
    </div>
  </body>
</html>
```

Or render individual fields:

```html
<form method="post">
  <Field field="{{ form.login }}" />
  <Field field="{{ form.password }}" />
  <Field field="{{ form.submit }}" />
</form>
```

## Usage

### Custom Field Rendering

Use the `render_kw` parameter to customize field HTML attributes:

```python
class ProfileForm(CherryForm):
    name = StringField(
        'Full Name',
        render_kw={
            "placeholder": "Enter your full name",
            "autofocus": "autofocus",
            "class": "custom-input",        # Applied to <input> tag
            'container-class': 'col-sm-6',  # Applied to <div> container
            'label-class': 'text-danger',   # Applied to <label>: class="text-danger"
            'label-attr': 'value'           # Applied to <label>: attr="value"
        },
    )
```

### JSON API Support

Handle JSON form submissions for API endpoints. This allow reeusing the same form to handle html form and api request. It's a good way to centralize the validation process.

It's also a good fit to leverage `form.strict_validate()` Validate that only known fields are submitted.

```python
@cherrypy.expose
@cherrypy.tools.allow(methods=['POST'])
@cherrypy.tools.json_out()
def api_login(self, **kwargs):
    form = LoginForm(json=True)  # Enable JSON parsing
    if form.strict_validate():
        # TODO Process login
        return {'success': True, 'user': form.login.data}
    else:
        # Return validation errors
        cherrypy.response.status = 400
        return {'success': False, 'errors': form.error_message}
```

**Client Request:**

```http
POST /api_login HTTP/1.1
Content-Type: application/json

{"login": "john", "password": "secret123"}
```

## Complete Example

```python
import cherrypy
from wtforms.fields import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Length, Email
from cherrypy_foundation.form import CherryForm
from cherrypy_foundation.flash import flash

env = cherrypy.tools.jinja2.create_env(
    package_name=__package__,
    globals={'get_flashed_messages': get_flashed_messages},
)

class RegistrationForm(CherryForm):
    username = StringField(
        'Username',
        validators=[InputRequired(), Length(min=3, max=20)],
        render_kw={"placeholder": "Choose a username"},
    )
    email = StringField(
        'Email',
        validators=[InputRequired(), Email()],
        render_kw={"placeholder": "your@email.com"},
    )
    password = PasswordField(
        'Password',
        validators=[InputRequired(), Length(min=8)],
        render_kw={"placeholder": "Choose a strong password"},
    )
    terms = BooleanField(
        'I agree to the Terms of Service',
        validators=[InputRequired()],
    )
    submit = SubmitField('Register', render_kw={"class": "btn-primary"})


@cherrypy.tools.sessions(locking='explicit')
@cherrypy.tools.jinja2(env=env)
class Root:
    
    @cherrypy.expose
    @cherrypy.tools.jinja2(template='register.html')
    def register(self, **kwargs):
        form = RegistrationForm()
        
        if form.validate_on_submit():
            # Create user account
            username = form.username.data
            email = form.email.data
            # TODO: Hash password, save to database
            flash(f'Welcome, {username}!', level='success')
            raise cherrypy.HTTPRedirect('/dashboard')
        if form.error_message:
            flash(form.error_message)
        return {'form': form}

if __name__ == '__main__':
    cherrypy.quickstart(Root())
```

**Template: `register.html`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Register</title>
    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
    <script src="/static/js/bootstrap.bundle.min.js"></script>
  </head>
  <body>
    <div class="container mt-5">
      <div class="row justify-content-center">
        <div class="col-md-6">
          <h2>Create Account</h2>
          
          <form method="post">
            {# Automatically render all form fields with Bootstrap styling #}
            <Fields form="{{ form }}" />
          </form>
          
          <p class="mt-3">
            Already have an account? <a href="/login">Login here</a>
          </p>
        </div>
      </div>
    </div>
  </body>
</html>
```
