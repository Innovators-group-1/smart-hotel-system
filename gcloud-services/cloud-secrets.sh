#!/bin/bash

ENV_FILE="smart_hotel_system/.env"
PROJECT_ID="quickdine-489018"

echo "📦 Uploading secrets to Google Secret Manager..."

while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  value=$(echo "$value" | sed "s/^['\"]//;s/['\"]$//")

  if gcloud secrets describe "$key" --project="$PROJECT_ID" &>/dev/null; then
    echo "🔄 Updating: $key"
    echo -n "$value" | gcloud secrets versions add "$key" --data-file=-
  else
    echo "✅ Creating: $key"
    echo -n "$value" | gcloud secrets create "$key" --data-file=- --project="$PROJECT_ID"
  fi

done < "$ENV_FILE"

echo "🎉 Done! All secrets uploaded."

# stephen-nyansoho-machera@stephen-ThinkPad-X280:~/Desktop/Smart-hotel/smart-hotel-system$ chmod +x gcloud-services/cloud-secrets.sh