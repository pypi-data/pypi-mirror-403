# notebook-frontend

A Python package distributing Notebook's static assets only, with no Python dependency.

```bash
git clean -fdx
curl --output notebook-7.5.3-py3-none-any.whl https://files.pythonhosted.org/packages/96/98/9286e7f35e5584ebb79f997f2fb0cb66745c86f6c5fccf15ba32aac5e908/notebook-7.5.3-py3-none-any.whl
unzip notebook-7.5.3-py3-none-any.whl
mkdir -p share
cp -r notebook-7.5.3.data/data/share/jupyter share/
cp -r notebook/static src/notebook_frontend/
cp -r notebook/templates src/notebook_frontend/
hatch build
hatch publish
```
