# os.py

Operating system utilities for checking the runtime environment.

- **Sudo**: Determine if the current process is running with `sudo`.
- **Internet connection**: Test for an internet connection.

## Example Usage

### Check for `sudo` privileges.

*python*

```python
if is_sudo():
    print("Running with sudo privileges.")
else:
    print("Running without sudo privileges.")
```

### Check for a live internet connection.

*python*

```python
if internet():
    print("An internet connection is available.")
else:
    print("No internet connection or DNS is blocked.")
```

Specify a host and port to check for specific services.

*python*

```python
# Check for a local web server
if internet(host='localhost', port=8000):
    print("Local web server is accessible.")
else:
    print("Local web server is not accessible.")
```
