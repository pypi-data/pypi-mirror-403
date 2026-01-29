test triton

## Clear the local cache 
rm -rf dist/*

## Build 
``` uv build ```

## publish 

Update the version in pyproject.xml

``` uv publish --token xxx ```
