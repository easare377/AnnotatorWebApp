import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from your_app.models import ImageMetadata, Missions


def extract_image_metadata(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()  # Get EXIF data
        if not exif_data:
            return {}

        metadata = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                gps_data = {}
                for gps_tag, gps_value in value.items():
                    gps_name = GPSTAGS.get(gps_tag, gps_tag)
                    gps_data[gps_name] = gps_value
                metadata["GPSInfo"] = gps_data
            else:
                metadata[tag_name] = value

        return metadata
    except Exception as e:
        print(f"Error reading metadata for {image_path}: {e}")
        return {}


def save_images_to_db(mission_id, folder_path):
    try:
        mission = Missions.objects.get(id=mission_id)

        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)

            # Skip non-image files
            if not file_name.lower().endswith(("jpg", "jpeg", "png")):
                continue

            metadata = extract_image_metadata(file_path)

            # Extract required fields from metadata
            latitude = metadata.get("GPSInfo", {}).get("GPSLatitude", None)
            longitude = metadata.get("GPSInfo", {}).get("GPSLongitude", None)
            date = metadata.get("DateTime", None)

            # Convert GPS coordinates to decimal if available
            def convert_to_decimal(coord):
                return coord[0] + coord[1] / 60 + coord[2] / 3600 if coord else None

            latitude = convert_to_decimal(latitude)
            longitude = convert_to_decimal(longitude)

            # Save to ImageMetadata model
            ImageMetadata.objects.create(
                mission=mission,
                latitude=latitude,
                longitude=longitude,
                date=date,
                image=file_name,
            )

    except Missions.DoesNotExist:
        print("Mission not found")
    except Exception as e:
        print(f"Error saving images to database: {e}")
