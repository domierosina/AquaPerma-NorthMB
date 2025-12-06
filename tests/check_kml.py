from fastkml import kml

with open("data/aoi/2025_aoi.kml", "rb") as f:
    doc = f.read()

k = kml.KML()
k.from_string(doc)

def print_features(features, level=0):
    for feature in features:
        print("  " * level, feature.name, feature.__class__)
        if hasattr(feature, 'features'):
            print_features(feature.features, level + 1)

# top-level features
print_features(k.features)
