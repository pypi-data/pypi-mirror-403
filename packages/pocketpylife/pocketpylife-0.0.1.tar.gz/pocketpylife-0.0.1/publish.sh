cd src
rm -rf pocketlife
git clone https://github.com/PKTwentyTwo/pocketpylife
cd ..
python3 -m build
cat pypi-API | python3 -m twine upload --repository pypi dist/*
pip install --upgrade pocketlife