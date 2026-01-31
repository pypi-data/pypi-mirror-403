"""
E2E test for batch uploads with dict syntax for per-video names.

Run with:
    python tests/upload_batch_dict_e2e.py
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
    folder_name = "akhil"

    # Batch upload with dict syntax for per-video names
    batch_items = [
        {"video": video_path, "name": "AAAA_batch_test_1.mp4"},
        {"video": video_path, "name": "AAAA_batch_test_2.mp4"},
    ]

    print("Batch uploading with dict syntax:")
    for item in batch_items:
        print(f"  - {item['name']}")
    print(f"Folder: {folder_name}")
    print()

    response = client.video.upload(
        batch_items,
        folder=folder_name,
        wait_for_uploaded=True,
    )

    print(f"Uploaded {len(response)} videos:")
    for r in response:
        print(f"  -> {r['video_id']}")

    # Verify the videos appear with correct names
    print("\nVerifying...")
    folder_videos = client.video.my_videos(folder=folder_name)

    expected_names = {item["name"] for item in batch_items}
    found_names = set()

    for v in folder_videos:
        video_name = v.get("video_name")
        if video_name in expected_names:
            print(f"  video_id: {v['video_id']}")
            print(f"  video_name: {video_name}")
            found_names.add(video_name)

    if found_names == expected_names:
        print("\nSUCCESS: All videos uploaded with correct names")
    else:
        missing = expected_names - found_names
        print(f"\nFAIL: Missing videos with names: {missing}")
        sys.exit(1)


if __name__ == "__main__":
    main()
