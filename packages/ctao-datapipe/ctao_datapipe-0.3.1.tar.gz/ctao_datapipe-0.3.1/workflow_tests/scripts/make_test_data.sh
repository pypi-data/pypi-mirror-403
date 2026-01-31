#!/usr/bin/env sh

# test data should be fetched using e.g.:

mkdir -p build
for p in gamma proton electron; do
    echo "Merging ${p}..."
    ctapipe-merge -o build/${p}_test_geo.dl2.h5 ${p}_*.DL2.h5
    echo "Applying ${p}..."
    ctapipe-apply-models -i build/${p}_test_geo.dl2.h5 \
        --output build/${p}_test_geo_en_cl.dl2.h5 \
        --reconstructor energy_model.pkl \
        --reconstructor classifier_model.pkl
done
