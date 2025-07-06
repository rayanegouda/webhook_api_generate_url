ID=222
AUTH=$(curl -s -X POST "http://machines.vmascourse.com/guacamole/api/tokens" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=guacadmin&password=guacadmin")
TOKEN=$(echo $AUTH | jq -r '.authToken')
CLIENT=$(echo -e -n "${ID}\tc\tmysql" | base64 | tr -d '=')
echo "http://machines.vmascourse.com/guacamole/#/client/"$CLIENT?token=$TOKEN
echo "http://machines.vmascourse.com/guacamole/#/client/c/"$ID?token=$TOKEN
