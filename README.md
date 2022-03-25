# Dremio Api Wrapper
Wrapper to use Dremio REST API in Python applications.

## Example
```
dremio_wrapper = DremioWrapper(host='', username='', password='')
dremio_wrapper.create_element(element_type='folder', element_name_or_path='folder.subfolder')
```