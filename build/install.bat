if exist env\ (
  echo "Yes, exists"
) else (
  echo "No, does not exist"
)

env\Scripts\activate
pip install -r build\module-requirements.txt