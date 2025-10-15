OS=mac
FILENAME=magicpod-api-client
curl -L "https://app.magicpod.com/api/v1.0/magicpod-clients/api/${OS}/latest/" -H "Authorization: Token ${MAGICPOD_API_TOKEN}" --output ${FILENAME}.zip
unzip -q ${FILENAME}.zip
