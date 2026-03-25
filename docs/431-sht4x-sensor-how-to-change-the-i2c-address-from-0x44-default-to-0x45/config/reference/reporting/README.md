# reporting :id=reporting

Configuration for reporting back to the developers using
[Sentry](https://sentry.io/welcome/) to help diagnose issues.

*This is **not** enabled by default*


```yaml
Type: dict
Required: False
```

?> Your config file is included in the report, but has the host, port and username
hashed and the password removed. Sentry's SDK automatically attempts to remove
password data, but the other values may still be exposed within the Python traceback
context.


**Example**:

```yaml
reporting:
  enabled: yes
  issue_id: 123
```

## enabled :id=reporting-enabled

*reporting*.**enabled**

Enable the sending of error reports to the developers if the software crashes.


```yaml
Type: boolean
Required: True
```

## issue_id :id=reporting-issue_id

*reporting*.**issue_id**

The GitHub Issue ID that the specific error relates to.

```yaml
Type: integer
Required: False
```

?> This is useful if you've reported a specific issue on the project repository and
want to provide additional context to help the developers diagnose the issue.


