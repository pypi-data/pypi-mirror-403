#!/usr/bin/env sh

NUM_FILES=4

for p in gamma electron proton; do
    dirac-dms-find-lfns array_layout=Alpha site=LaPalma \
        MCCampaign=PROD6 outputType=Data analysis_prog_version=v0.23.1 \
        analysis_prog=ctapipe-process data_level=2 \
        particle=$p | head -$NUM_FILES >> event_lfns.txt
done

dirac-dms-find-lfns  array_layout=Alpha site=LaPalma \
    MCCampaign=PROD6 outputType=Model > model_lfns.txt

cta-prod-get-file model_lfns.txt
cta-prod-get-file event_lfns.txt
