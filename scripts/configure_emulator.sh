gcloud config configurations create emulator
gcloud config set auth/disable_credentials true
gcloud config set project ${PROJECT_ID}
gcloud config set api_endpoint_overrides/spanner ${SPANNER_EMULATOR_URL}
gcloud spanner instances create ${INSTANCE_NAME} --config=emulator-config --description=Emulator --nodes=1