"""
E2E test for URL uploads with custom name parameter.

Run with:
    python tests/upload_url_with_name_e2e.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nomadicml import NomadicML


def main():
    client = NomadicML(
        api_key="sk_ODjeqIJ9yOVPieL6SN4Jg1pXngHGDh1eoMRSQktdPoT5hN40",
        base_url="http://localhost:8099",
        collection_name="videos_dev",
        folder_collection_name="videoFolders_dev",
    )

    # Public sample video URL
    video_url = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
    custom_name = "AAAA_url_test_custom_name.mp4"
    folder_name = "akhil"

    print(f"Uploading URL: {video_url}")
    print(f"Custom name: {custom_name}")
    print(f"Folder: {folder_name}")
    print()

    # Upload URL with custom name
    response = client.video.upload(
        video_url,
        name=custom_name,
        folder=folder_name,
        wait_for_uploaded=True,
    )
    video_id = response["video_id"]
    print(f"Uploaded video_id: {video_id}")

    # Verify the video appears with correct name
    print("\nVerifying...")
    folder_videos = client.video.my_videos(folder=folder_name)

    for v in folder_videos:
        if v["video_id"] == video_id:
            print(f"  video_id: {v['video_id']}")
            print(f"  video_name: {v.get('video_name')}")
            print(f"  folder_name: {v.get('folder_name')}")

            assert v.get("video_name") == custom_name, f"Expected {custom_name}, got {v.get('video_name')}"
            assert v.get("folder_name") == folder_name, f"Expected {folder_name}, got {v.get('folder_name')}"

            print("\nSUCCESS: URL uploaded with correct custom name")
            return

    print("FAIL: Video not found in folder")
    sys.exit(1)


if __name__ == "__main__":
    main()
