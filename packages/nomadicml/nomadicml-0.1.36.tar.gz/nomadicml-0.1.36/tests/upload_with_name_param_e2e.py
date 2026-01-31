"""
E2E test for the `name` parameter in client.video.upload().

Run with:
    python tests/upload_with_name_param_e2e.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nomadicml import NomadicML


def main():
    client = NomadicML(
        api_key="sk_ODjeqIJ9yOVPieL6SN4Jg1pXngHGDh1eoMRSQktdPoT5hN40",
        base_url="https://api.nomadicml.com",
        collection_name="videos_dev",
        folder_collection_name="videoFolders_dev",
    )

    video_path = "/Users/aaparvat/Downloads/banana_man.mp4"
    custom_name = "000akhil_test.mp4"
    folder_name = "akhil"

    print(f"Uploading: {video_path}")
    print(f"Name: {custom_name}")
    print(f"Folder: {folder_name}")
    print()

    # Upload with custom name to folder
    response = client.video.upload(
        video_path,
        name=custom_name,
        folder=folder_name,
        wait_for_uploaded=True,
    )
    video_id = response["video_id"]
    print(f"Uploaded video_id: {video_id}")

    # Verify the video appears with correct name and folder
    print("\nVerifying...")
    folder_videos = client.video.my_videos(folder=folder_name)

    for v in folder_videos:
        if v["video_id"] == video_id:
            print(f"  video_id: {v['video_id']}")
            print(f"  video_name: {v.get('video_name')}")
            print(f"  folder_name: {v.get('folder_name')}")

            assert v.get("video_name") == custom_name, f"Expected {custom_name}, got {v.get('video_name')}"
            assert v.get("folder_name") == folder_name, f"Expected {folder_name}, got {v.get('folder_name')}"

            print("\nSUCCESS: Video uploaded with correct name and folder")
            return

    print("FAIL: Video not found in folder")
    sys.exit(1)


if __name__ == "__main__":
    main()
